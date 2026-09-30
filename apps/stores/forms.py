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
            "mx_accepts_spei", "mx_accepts_mercadopago", "mx_accepts_paypal",
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
            "mx_accepts_spei": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "mx_accepts_mercadopago": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "mx_accepts_paypal": forms.CheckboxInput(attrs={"class": "form-check-input"}),
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
            "mx_accepts_spei": "Acepto transferencia SPEI",
            "mx_accepts_mercadopago": "Acepto Mercado Pago",
            "mx_accepts_paypal": "Acepto PayPal",
            "offers_delivery": "Ofrecer delivery a domicilio",
            "delivery_fee": "Tarifa de delivery (USD)",
        }

    def __init__(self, *args, **kwargs):
        """
        Oculta los campos que no aplican a la region del comercio.
        - VE: oculta toggles MX
        - MX: oculta toggles VE
        """
        super().__init__(*args, **kwargs)
        region = getattr(self.instance, "payment_region", "VE") or "VE"

        if region == "VE":
            for nombre in ["mx_accepts_spei", "mx_accepts_mercadopago", "mx_accepts_paypal"]:
                self.fields.pop(nombre, None)
        elif region == "MX":
            for nombre in ["accepts_transfer", "accepts_mobile_payment"]:
                self.fields.pop(nombre, None)

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
    """
    Formulario para que el owner solicite el cambio de datos bancarios.

    Los campos mostrados dependen de la region del comercio (payment_region):
    - VE: usa los campos new_bank_name, new_account_number, etc.
    - MX: usa los campos new_mx_accepts_spei, new_mx_spei_clabe, etc.
    """

    class Meta:
        model = StorePaymentChangeRequest
        fields = [
            # Venezuela
            "new_bank_name", "new_account_number", "new_account_holder",
            "new_document",
            "new_mobile_payment_bank", "new_mobile_document", "new_payment_phone",
            # Mexico
            "new_mx_accepts_spei",
            "new_mx_spei_clabe", "new_mx_spei_holder", "new_mx_spei_bank",
            "new_mx_accepts_mercadopago",
            "new_mx_mercadopago_alias",
            "new_mx_accepts_paypal",
            "new_mx_paypal_email",
            "new_mx_payment_notes",
            # Comun
            "reason",
        ]
        widgets = {
            # ===== VE =====
            "new_bank_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Banesco",
            }),
            "new_account_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: 0134-1234-56-78901234",
            }),
            "new_account_holder": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nombre completo del titular",
            }),
            "new_document": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "V-12345678 o J-12345678-9",
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
            # ===== MX - SPEI =====
            "new_mx_accepts_spei": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "new_mx_spei_clabe": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "18 digitos, ej: 012180001234567890",
                "maxlength": "18",
            }),
            "new_mx_spei_holder": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nombre completo del titular",
            }),
            "new_mx_spei_bank": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: BBVA, Santander, Banorte",
            }),
            # ===== MX - Mercado Pago =====
            "new_mx_accepts_mercadopago": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "new_mx_mercadopago_alias": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Alias o CVU de Mercado Pago",
            }),
            # ===== MX - PayPal =====
            "new_mx_accepts_paypal": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "new_mx_paypal_email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "correo@ejemplo.com",
            }),
            # ===== MX - Notas =====
            "new_mx_payment_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Informacion adicional para el cliente mexicano (opcional)",
            }),
            # ===== Comun =====
            "reason": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Explica brevemente por que cambias estos datos",
            }),
        }
        labels = {
            # VE
            "new_bank_name": "Banco",
            "new_account_number": "Numero de cuenta",
            "new_account_holder": "Titular de la cuenta",
            "new_document": "Cedula/RIF",
            "new_mobile_payment_bank": "Banco receptor (pagomovil)",
            "new_mobile_document": "Cedula/RIF (pagomovil)",
            "new_payment_phone": "Telefono (pagomovil)",
            # MX
            "new_mx_accepts_spei": "Acepto transferencia SPEI",
            "new_mx_spei_clabe": "CLABE interbancaria (18 digitos)",
            "new_mx_spei_holder": "Titular de la CLABE",
            "new_mx_spei_bank": "Banco de la CLABE",
            "new_mx_accepts_mercadopago": "Acepto Mercado Pago",
            "new_mx_mercadopago_alias": "Alias / CVU de Mercado Pago",
            "new_mx_accepts_paypal": "Acepto PayPal",
            "new_mx_paypal_email": "Email de PayPal",
            "new_mx_payment_notes": "Notas adicionales (MX)",
            # Comun
            "reason": "Motivo del cambio",
        }

    def __init__(self, *args, store=None, **kwargs):
        """
        Acepta un kwarg opcional 'store'. Si no viene, intenta leerlo
        desde self.instance.store. Si no puede, asume region VE.
        """
        super().__init__(*args, **kwargs)

        # Determinar region
        if store is not None:
            self.region = getattr(store, "payment_region", "VE") or "VE"
        elif self.instance and self.instance.pk and self.instance.store_id:
            try:
                self.region = self.instance.store.payment_region or "VE"
            except Exception:
                self.region = "VE"
        else:
            self.region = "VE"

    def clean(self):
        cleaned = super().clean()
        if self.region == "MX":
            return self._clean_mx(cleaned)
        return self._clean_ve(cleaned)

    def _clean_ve(self, cleaned):
        """Validacion para comercios venezolanos (comportamiento original)."""
        change_fields = [
            "new_bank_name", "new_account_number", "new_account_holder",
            "new_document", "new_mobile_payment_bank", "new_mobile_document",
            "new_payment_phone",
        ]
        has_any = any(cleaned.get(f) for f in change_fields)

        if not has_any:
            raise forms.ValidationError(
                "Debes indicar al menos un cambio en los datos bancarios."
            )

        # Validacion en grupo de pago movil
        pm_bank = (cleaned.get("new_mobile_payment_bank") or "").strip()
        pm_doc = (cleaned.get("new_mobile_document") or "").strip()
        pm_phone = (cleaned.get("new_payment_phone") or "").strip()

        pm_llenos = sum(1 for c in [pm_bank, pm_doc, pm_phone] if c)

        if 0 < pm_llenos < 3:
            if not pm_bank:
                self.add_error("new_mobile_payment_bank", "Requerido si actualizas pago movil.")
            if not pm_doc:
                self.add_error("new_mobile_document", "Requerido si actualizas pago movil.")
            if not pm_phone:
                self.add_error("new_payment_phone", "Requerido si actualizas pago movil.")
            raise forms.ValidationError(
                "Debes completar los 3 campos de pago movil (Banco, Cedula/RIF y Telefono) "
                "o dejar los 3 vacios."
            )

        return cleaned

    def _clean_mx(self, cleaned):
        """Validacion para comercios mexicanos."""
        import re as _re

        spei = cleaned.get("new_mx_accepts_spei")
        mp = cleaned.get("new_mx_accepts_mercadopago")
        pp = cleaned.get("new_mx_accepts_paypal")

        # Al menos un metodo activo o algun cambio
        hay_datos = any([
            cleaned.get("new_mx_spei_clabe"),
            cleaned.get("new_mx_mercadopago_alias"),
            cleaned.get("new_mx_paypal_email"),
            cleaned.get("new_mx_payment_notes"),
        ])

        if not any([spei, mp, pp]) and not hay_datos:
            raise forms.ValidationError(
                "Debes activar al menos un metodo de pago o cambiar algun dato."
            )

        # SPEI
        if spei:
            clabe = (cleaned.get("new_mx_spei_clabe") or "").strip()
            holder = (cleaned.get("new_mx_spei_holder") or "").strip()
            bank = (cleaned.get("new_mx_spei_bank") or "").strip()

            if not clabe:
                self.add_error("new_mx_spei_clabe", "CLABE requerida si activas SPEI.")
            elif not _re.match(r"^\d{18}$", clabe):
                self.add_error(
                    "new_mx_spei_clabe",
                    "La CLABE debe tener exactamente 18 digitos numericos."
                )
            if not holder:
                self.add_error("new_mx_spei_holder", "Titular requerido si activas SPEI.")
            if not bank:
                self.add_error("new_mx_spei_bank", "Banco requerido si activas SPEI.")

        # Mercado Pago
        if mp:
            alias = (cleaned.get("new_mx_mercadopago_alias") or "").strip()
            if not alias:
                self.add_error(
                    "new_mx_mercadopago_alias",
                    "Alias requerido si activas Mercado Pago."
                )

        # PayPal
        if pp:
            email = (cleaned.get("new_mx_paypal_email") or "").strip()
            if not email:
                self.add_error(
                    "new_mx_paypal_email",
                    "Email requerido si activas PayPal."
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
