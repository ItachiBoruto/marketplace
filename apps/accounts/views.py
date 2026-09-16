from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .forms import CustomUserCreationForm
from .models import UserProfile
from .tokens import (
    decode_token_from_url,
    encode_token_for_url,
    generate_email_verification_token,
    verify_email_token,
)


# ============================================================
# Helpers
# ============================================================
def _send_verification_email(user, request):
    """Envia el correo de verificacion al usuario."""
    token = generate_email_verification_token(user)
    encoded_token = encode_token_for_url(token)
    verify_url = request.build_absolute_uri(
        reverse("accounts:verify_email", args=[encoded_token])
    )

    subject = "Verifica tu correo en Mi Marketplace"
    text_body = f"Hola {user.username}, verifica tu correo aqui: {verify_url}"
    html_body = render_to_string(
        "emails/verify_email.html",
        {"username": user.username, "verify_url": verify_url},
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@marketplace.local")
    msg = EmailMultiAlternatives(subject, text_body, from_email, [user.email])
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)

    # Registrar fecha de envio
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.last_verification_sent_at = timezone.now()
    profile.save(update_fields=["last_verification_sent_at"])


# ============================================================
# Registro
# ============================================================
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="apps.accounts.backends.EmailOrUsernameBackend")

            # Enviar email de verificacion (no bloquea si falla)
            try:
                _send_verification_email(user, request)
                messages.info(
                    request,
                    f"Te enviamos un correo a {user.email}. "
                    "Haz clic en el enlace para verificar tu cuenta."
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).exception("Error enviando verificacion: %s", e)
                messages.warning(
                    request,
                    "Te registraste, pero no pudimos enviar el correo de verificación. "
                    "Puedes pedir uno nuevo desde tu perfil."
                )

            return redirect("/")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})


# ============================================================
# Verificacion de email
# ============================================================
def verify_email(request, token):
    """Vista que verifica el token y marca el email como verificado."""
    # Decodificar el token que viene URL-encoded
    real_token = decode_token_from_url(token)
    data = verify_email_token(real_token)

    if data is None or "error" in data:
        error = data.get("error") if data else "invalid"
        return render(request, "registration/email_verification_invalid.html", {
            "error": error,
        })

    user_id = data.get("user_id")
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return render(request, "registration/email_verification_invalid.html", {
            "error": "user_not_found",
        })

    profile, _ = UserProfile.objects.get_or_create(user=user)

    if profile.email_verified:
        # Ya verificado - idempotente
        return render(request, "registration/email_verified.html", {
            "user": user,
            "already_verified": True,
        })

    profile.email_verified = True
    profile.email_verified_at = timezone.now()
    profile.save(update_fields=["email_verified", "email_verified_at"])

    return render(request, "registration/email_verified.html", {
        "user": user,
        "already_verified": False,
    })


# ============================================================
# Reenviar verificacion
# ============================================================
@login_required(login_url="login")
def resend_verification(request):
    """Reenvia el correo de verificacion con rate limiting."""
    if request.method != "POST":
        return redirect("/")

    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if profile.email_verified:
        messages.info(request, "Tu correo ya está verificado.")
        return redirect("/")

    if not user.email:
        messages.error(request, "Tu cuenta no tiene correo registrado.")
        return redirect("/")

    now = timezone.now()
    today = now.date()

    # Resetear contador si es un dia nuevo
    if profile.verification_attempts_date != today:
        profile.verification_attempts_today = 0
        profile.verification_attempts_date = today

    # Limite diario
    if profile.verification_attempts_today >= 5:
        messages.error(
            request,
            "Has alcanzado el límite de reenvíos por hoy. "
            "Intenta de nuevo mañana."
        )
        return redirect("/")

    # Cooldown de 5 min
    if profile.last_verification_sent_at:
        diff = (now - profile.last_verification_sent_at).total_seconds()
        if diff < 300:
            minutes = int((300 - diff) // 60) + 1
            messages.warning(
                request,
                f"Ya te enviamos un correo hace poco. "
                f"Espera ~{minutes} min para pedir otro."
            )
            return redirect("/")

    try:
        _send_verification_email(user, request)
        profile.verification_attempts_today += 1
        profile.save(update_fields=["verification_attempts_today", "verification_attempts_date"])
        messages.success(request, f"Correo reenviado a {user.email}.")
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Error reenviando verificacion: %s", e)
        messages.error(request, "No pudimos enviar el correo. Intenta de nuevo.")

    return redirect("/")


# ============================================================
# Endpoint de estado (para el banner)
# ============================================================
@login_required(login_url="login")
def verification_status(request):
    from django.http import JsonResponse
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return JsonResponse({
        "verified": profile.email_verified,
        "has_email": bool(request.user.email),
    })


# ============================================================
# Login personalizado
# ============================================================
class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_invalid(self, form):
        response = super().form_invalid(form)

        remaining = None
        try:
            from axes.handlers.proxy import AxesProxyHandler
            credentials = getattr(form, "cleaned_data", {}) or {}
            handler = AxesProxyHandler.get_implementation()
            failures = handler.get_failures(self.request, credentials)
            remaining = max(0, settings.AXES_FAILURE_LIMIT - failures)
        except Exception:
            remaining = None

        cooloff_minutes = 5
        try:
            cooloff_minutes = int(settings.AXES_COOLOFF_TIME.total_seconds() // 60)
        except Exception:
            pass

        if remaining is None:
            messages.warning(self.request, "Usuario o contraseña incorrectos. Intenta de nuevo.")
        elif remaining <= 0:
            messages.info(
                self.request,
                f"🕒 Por seguridad, hemos pausado los intentos durante {cooloff_minutes} minutos. "
                f"Podrás intentarlo de nuevo en un momento."
            )
        elif remaining == 1:
            messages.warning(
                self.request,
                f"Usuario o contraseña incorrectos. Te queda 1 intento. "
                f"Si no aciertas, podrás intentarlo de nuevo en {cooloff_minutes} minutos."
            )
        else:
            messages.warning(
                self.request,
                f"Usuario o contraseña incorrectos. Te quedan {remaining} intentos."
            )

        return response


def axes_lockout_response(request, credentials, *args, **kwargs):
    cooloff_minutes = 5
    try:
        cooloff_minutes = int(settings.AXES_COOLOFF_TIME.total_seconds() // 60)
    except Exception:
        pass

    messages.info(
        request,
        f"🕒 Por seguridad, hemos pausado los intentos durante {cooloff_minutes} minutos. "
        f"Podrás intentarlo de nuevo en un momento."
    )
    return redirect("login")
