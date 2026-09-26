import random
import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile
from .validators import validate_email_mx


class CustomUserCreationForm(UserCreationForm):
    """
    Formulario de registro con:
    - Username unico (case-insensitive)
    - Email unico (case-insensitive) + validacion MX
    - Telefono obligatorio
    """
    username = forms.CharField(
        min_length=3,
        max_length=30,
        required=True,
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "autocomplete": "username",
            "autocapitalize": "none",
            "autocorrect": "off",
            "spellcheck": "false",
            "pattern": "[a-zA-Z0-9]+",
            "title": "Solo letras y numeros",
        }),
        error_messages={
            "required": "El nombre de usuario es obligatorio.",
            "min_length": "El nombre de usuario debe tener al menos 3 caracteres.",
            "max_length": "El nombre de usuario no puede tener mas de 30 caracteres.",
        }
    )
    email = forms.EmailField(
        required=True,
        label="Correo electronico",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    terms_accepted = forms.BooleanField(
        required=True,
        label="Acepto los Términos y la Política de Privacidad",
        error_messages={
            "required": "Debes aceptar los Términos y la Política de Privacidad para registrarte."
        },
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sugerencias de username (se llenan si el username esta tomado)
        self.suggested_usernames = []

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()

        # Solo letras y numeros
        if not re.match(r"^[a-zA-Z0-9]+$", username):
            raise forms.ValidationError(
                "El nombre de usuario solo puede contener letras y numeros (sin espacios ni simbolos)."
            )

        # Verificar unicidad (case-insensitive)
        if User.objects.filter(username__iexact=username).exists():
            # Generar sugerencias para el template
            self.suggested_usernames = self._generate_username_suggestions(username)
            raise forms.ValidationError(
                "Ya existe una cuenta con este nombre de usuario. Prueba con una de las sugerencias."
            )

        return username

    def _generate_username_suggestions(self, base, count=3, max_len=30):
        """Genera sugerencias de username agregando numeros al final."""
        suggestions = []

        # 1) Intentar base + 2, base + 3, ... (corto)
        for i in range(2, 100):
            suffix = str(i)
            max_base_len = max_len - len(suffix)
            base_trimmed = base[:max_base_len] if len(base) > max_base_len else base
            candidate = base_trimmed + suffix
            if not User.objects.filter(username__iexact=candidate).exists():
                suggestions.append(candidate)
                if len(suggestions) >= count:
                    return suggestions

        # 2) Si todos los secuenciales estan tomados, usar numeros aleatorios
        intentos = 0
        while len(suggestions) < count and intentos < 50:
            intentos += 1
            suffix = str(random.randint(100, 9999))
            max_base_len = max_len - len(suffix)
            base_trimmed = base[:max_base_len] if len(base) > max_base_len else base
            candidate = base_trimmed + suffix
            if candidate in suggestions:
                continue
            if not User.objects.filter(username__iexact=candidate).exists():
                suggestions.append(candidate)

        return suggestions

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta registrada con este correo. "
                "Olvidaste tu contrasena?"
            )
        # Verificar que el dominio tenga servidor de correo (MX)
        validate_email_mx(email)
        return email

    def save(self, commit=True):
        from django.utils import timezone

        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "terms_accepted": True,
                    "terms_accepted_at": timezone.now(),
                    "terms_version": "v1.0",
                }
            )
        return user
