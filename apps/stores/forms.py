from django import forms

from .models import Store


class StoreProfileForm(forms.ModelForm):
    """Formulario para editar el perfil del comercio."""

    class Meta:
        model = Store
        fields = [
            "name", "logo", "description", "is_active",
            "legal_name", "rif", "address", "phone", "email",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "legal_name": forms.TextInput(attrs={"class": "form-control"}),
            "rif": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
        labels = {
            "name": "Nombre comercial",
            "logo": "Logo",
            "description": "Descripción",
            "is_active": "¿Activo?",
            "legal_name": "Razón social",
            "rif": "RIF",
            "address": "Dirección",
            "phone": "Teléfono (opcional)",
            "email": "Correo electrónico (opcional)",
        }
