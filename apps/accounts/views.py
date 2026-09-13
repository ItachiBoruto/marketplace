from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import CustomUserCreationForm


def register(request):
    """Registro público de usuarios."""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("/")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})


class CustomLoginView(LoginView):
    """Login con avisos amigables de intentos restantes (integración con django-axes)."""

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
            messages.warning(
                self.request,
                "Usuario o contraseña incorrectos. Intenta de nuevo."
            )
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
    """
    Cuando django-axes bloquea, en lugar de devolver 429/403,
    redirige al login con un mensaje amigable.
    """
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