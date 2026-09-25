from django import forms

from apps.utils.validators import validate_image

from .models import Store, StorePaymentChangeRequest


class StoreProfileForm(forms.ModelForm):
    """
    Formulario para editar el perfil del comercio.
    Los datos bancarios criticos NO se editan aqui (requieren aprobacion del superuser).
    Solo se pueden editar:
    - Datos generales del comercio
    - Metodos de pago aceptados (toggles)
    - Delivery
    """

    class Meta:
        model = Store
        fields = [
            "name", "logo", "description", "is_active",
            "legal_name", "rif", "address", "phone", "email",
            "accepts_transfer", "accepts_mobile_payment",
            "offers_delivery", "delivery_fee",
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
            "accepts_transfer": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "accepts_mobile_payment": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "offers_delivery": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "delivery_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
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
            "accepts_transfer": "Acepto transferencia bancaria",
            "accepts_mobile_payment": "Acepto pago móvil",
            "offers_delivery": "Ofrecer delivery a domicilio",
            "delivery_fee": "Tarifa de delivery (USD)",
        }

    def clean_logo(self):
        img = self.cleaned_data.get('logo')
        # Solo validar si es un archivo NUEVO subido ahora.
        from django.core.files.uploadedfile import UploadedFile
        if img and isinstance(img, UploadedFile) and img.size > 0:
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


class PaymentChangeRequestForm(forms.ModelForm):
    """Formulario para que el owner solicite el cambio de datos bancarios."""

    class Meta:
        model = StorePaymentChangeRequest
        fields = [
            "new_bank_name", "new_account_number", "new_account_holder",
            "new_document",
            "new_mobile_payment_bank", "new_mobile_document", "new_payment_phone",
            "reason",
        ]
        widgets = {
            "new_bank_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Banesco",
                "required": True,
            }),
            "new_account_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: 0134-1234-56-78901234",
                "required": True,
            }),
            "new_account_holder": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nombre completo del titular",
                "required": True,
            }),
            "new_document": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "V-12345678 o J-12345678-9",
                "required": True,
            }),
            "new_mobile_payment_bank": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Banesco o Venezuela 0102",
            }),
            "new_mobile_document": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "V-12345678 o J-12345678-9",
            }),
            "new_payment_phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "0414-1234567",
            }),
            "reason": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Explica brevemente por qué cambias estos datos (ej: cambio de banco, actualización de cuenta, etc.)",
                "required": True,
            }),
        }
        labels = {
            "new_bank_name": "Banco",
            "new_account_number": "Número de cuenta",
            "new_account_holder": "Titular de la cuenta",
            "new_document": "Cédula/RIF",
            "new_mobile_payment_bank": "Banco receptor",
            "new_mobile_document": "Cédula/RIF",
            "new_payment_phone": "Teléfono",
            "reason": "Motivo del cambio",
        }

    def clean(self):
        cleaned = super().clean()

        # Verificar que al menos un campo cambió
        change_fields = [
            'new_bank_name', 'new_account_number', 'new_account_holder',
            'new_document', 'new_mobile_payment_bank', 'new_mobile_document', 'new_payment_phone',
        ]
        has_any = any(cleaned.get(f) for f in change_fields)

        if not has_any:
            raise forms.ValidationError(
                'Debes indicar al menos un cambio en los datos bancarios.'
            )

        # ============================================================
        # Validacion EN GRUPO de los datos de pago movil:
        # o se completan los 3, o no se completa ninguno.
        # ============================================================
        pm_bank = (cleaned.get('new_mobile_payment_bank') or '').strip()
        pm_doc = (cleaned.get('new_mobile_document') or '').strip()
        pm_phone = (cleaned.get('new_payment_phone') or '').strip()

        pm_campos = [pm_bank, pm_doc, pm_phone]
        pm_llenos = sum(1 for c in pm_campos if c)

        if 0 < pm_llenos < 3:
            # Alguno lleno pero no todos
            if not pm_bank:
                self.add_error('new_mobile_payment_bank', 'Requerido si actualizas pago movil.')
            if not pm_doc:
                self.add_error('new_mobile_document', 'Requerido si actualizas pago movil.')
            if not pm_phone:
                self.add_error('new_payment_phone', 'Requerido si actualizas pago movil.')
            raise forms.ValidationError(
                'Debes completar los 3 campos de pago movil (Banco, Cedula/RIF y Telefono) '
                'o dejar los 3 vacios.'
            )

        return cleaned


class ScheduleForm(forms.ModelForm):
    """Formulario para editar un dia de horario."""

    class Meta:
        from .models import StoreSchedule
        model = StoreSchedule
        fields = [
            'is_closed',
            'pickup_open', 'pickup_close',
            'delivery_open', 'delivery_close',
        ]
        widgets = {
            'is_closed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pickup_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'pickup_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'delivery_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'delivery_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }
        labels = {
            'is_closed': 'Cerrado este día',
            'pickup_open': 'Retiro abre',
            'pickup_close': 'Retiro cierra',
            'delivery_open': 'Delivery abre',
            'delivery_close': 'Delivery cierra',
        }

    def clean(self):
        cleaned = super().clean()
        is_closed = cleaned.get('is_closed')

        if is_closed:
            # Si esta cerrado, ignorar horarios
            return cleaned

        # Validar rangos de retiro
        p_open = cleaned.get('pickup_open')
        p_close = cleaned.get('pickup_close')
        if p_open and p_close:
            # Permitimos rangos que cruzan medianoche
            pass  # Sin restriccion estricta

        # Validar que si pone un campo, ponga el otro
        if (p_open and not p_close) or (p_close and not p_open):
            self.add_error('pickup_close', 'Debes especificar ambas horas de retiro.')

        d_open = cleaned.get('delivery_open')
        d_close = cleaned.get('delivery_close')
        if (d_open and not d_close) or (d_close and not d_open):
            self.add_error('delivery_close', 'Debes especificar ambas horas de delivery.')

        return cleaned
