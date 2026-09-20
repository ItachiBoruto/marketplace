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
    email = forms.EmailField(
        required=True,
        label="Correo electronico",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        label="Telefono",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    terms_accepted = forms.BooleanField(
        required=True,
        label="Acepto los Términos y la Política de Privacidad",
        error_messages={
            "required": "Debes aceptar los Términos y la Política de Privacidad para registrarte."
        },
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta con este nombre de usuario."
            )
        return username

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
                    "phone": self.cleaned_data["phone"],
                    "terms_accepted": True,
                    "terms_accepted_at": timezone.now(),
                    "terms_version": "v1.0",
                }
            )
        return user
