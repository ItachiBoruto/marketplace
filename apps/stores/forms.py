from django import forms

from apps.utils.validators import validate_image

from .models import Store


class StoreProfileForm(forms.ModelForm):
    """Formulario para editar el perfil del comercio."""

    class Meta:
        model = Store
        fields = [
            "name", "logo", "description", "is_active",
            "legal_name", "rif", "address", "phone", "email",
            "offers_delivery", "delivery_fee",
            "bank_name", "account_number", "account_holder",
            "document", "payment_phone", "payment_email", "payment_notes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "legal_name": forms.TextInput(attrs={"class": "form-control"}),
            "rif": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "offers_delivery": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "delivery_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "bank_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Banesco"}),
            "account_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: 0134-1234-56-78901234"}),
            "account_holder": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre completo"}),
            "document": forms.TextInput(attrs={"class": "form-control", "placeholder": "V-12345678 o J-12345678-9"}),
            "payment_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "0414-1234567"}),
            "payment_email": forms.EmailInput(attrs={"class": "form-control"}),
            "payment_notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
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
            "offers_delivery": "Ofrecer delivery a domicilio",
            "delivery_fee": "Tarifa de delivery (USD)",
            "bank_name": "Banco",
            "account_number": "Número de cuenta",
            "account_holder": "Titular de la cuenta",
            "document": "Cédula o RIF",
            "payment_phone": "Teléfono para pago móvil",
            "payment_email": "Email para notificaciones de pago",
            "payment_notes": "Notas adicionales",
        }

    def clean_logo(self):
        img = self.cleaned_data.get('logo')
        if img and hasattr(img, 'size'):
            validate_image(img)
        return img

    def clean(self):
        cleaned = super().clean()
        offers = cleaned.get('offers_delivery')
        fee = cleaned.get('delivery_fee') or 0

        if offers and fee <= 0:
            self.add_error(
                'delivery_fee',
                'Debes indicar una tarifa mayor a 0 si ofreces delivery.'
            )

        return cleaned
