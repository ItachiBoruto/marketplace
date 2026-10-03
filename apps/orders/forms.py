import re

from django import forms

from apps.utils.validators import validate_image

from .models import Order, OrderClaim, OrderClaimMessage


class PaymentForm(forms.ModelForm):
    """Formulario donde el cliente reporta los datos de su pago."""

    class Meta:
        model = Order
        fields = (
            'shipping_method', 'delivery_address',
            'payment_method',
            'payment_bank', 'payment_reference', 'payment_date',
            'payment_proof', 'notes',
        )
        widgets = {
            'shipping_method': forms.RadioSelect(attrs={'class': 'shipping-radio'}),
            'payment_method': forms.RadioSelect(attrs={'class': 'payment-radio'}),
            'delivery_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Ej: Av. Principal, Casa 12, sector Centro, frente a la panadería',
            }),
            'payment_bank': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Banco de Venezuela, Banesco, etc.'
            }),
            'payment_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Solo números (4 a 12 dígitos)',
                'inputmode': 'numeric',
                'pattern': '[0-9]{4,12}',
                'maxlength': '12',
                'minlength': '4',
                'autocomplete': 'off',
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_proof': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Alguna nota adicional para el vendedor (opcional)'
            }),
        }
        labels = {
            'shipping_method': '¿Cómo quieres recibir tu pedido?',
            'payment_method': '¿Cómo quieres pagar?',
            'delivery_address': 'Dirección de entrega',
            'payment_bank': 'Banco emisor',
            'payment_reference': 'Número de referencia',
            'payment_date': 'Fecha del pago',
            'payment_proof': 'Comprobante (imagen)',
            'notes': 'Notas (opcional)',
        }

    def __init__(self, *args, **kwargs):
        self.delivery_available = kwargs.pop('delivery_available', False)
        self.pickup_available = kwargs.pop('pickup_available', True)
        self.accepts_transfer = kwargs.pop('accepts_transfer', True)
        self.accepts_mobile = kwargs.pop('accepts_mobile', False)
        self.accepts_spei = kwargs.pop('accepts_spei', False)
        self.accepts_mercadopago = kwargs.pop('accepts_mercadopago', False)
        self.accepts_paypal = kwargs.pop('accepts_paypal', False)
        self.payment_region = kwargs.pop('payment_region', 'VE')
        super().__init__(*args, **kwargs)

        # Construir dinamicamente las opciones disponibles
        choices = []
        if self.pickup_available:
            choices.append(('pickup', 'Retiro en tienda'))
        if self.delivery_available:
            choices.append(('delivery', 'Delivery a domicilio'))

        # Si no hay ninguna, dejar pickup por defecto (aunque se bloqueara antes)
        if not choices:
            choices = [('pickup', 'Retiro en tienda')]

        self.fields['shipping_method'].choices = choices

        # Seleccionar el primer metodo disponible por defecto
        self.fields['shipping_method'].initial = choices[0][0]

        # ===== Choices de metodo de PAGO (segun region) =====
        payment_choices = []
        if self.payment_region == 'MX':
            if self.accepts_spei:
                payment_choices.append(('spei', 'Transferencia SPEI'))
            if self.accepts_mercadopago:
                payment_choices.append(('mercadopago', 'Mercado Pago'))
            if self.accepts_paypal:
                payment_choices.append(('paypal', 'PayPal'))
        else:
            # VE (default)
            if self.accepts_transfer:
                payment_choices.append(('transfer', 'Transferencia bancaria'))
            if self.accepts_mobile:
                payment_choices.append(('mobile', 'Pago movil'))

        # Si el comercio no acepta ninguno -> no permitir envio
        if not payment_choices:
            raise forms.ValidationError(
                'El comercio no tiene metodos de pago configurados. Contacta al vendedor.'
            )

        self.fields['payment_method'].choices = payment_choices
        self.fields['payment_method'].initial = payment_choices[0][0]

        # Ajustar labels segun region
        if self.payment_region == 'MX':
            self.fields['payment_bank'].label = 'Banco emisor (SPEI)'
            self.fields['payment_bank'].widget.attrs['placeholder'] = 'Ej: BBVA, Santander, Banorte'
            self.fields['payment_reference'].label = 'Clave de rastreo / ID de operacion'
            self.fields['payment_reference'].widget.attrs['placeholder'] = 'Ej: MBAN0100240913XXXX o ID de Mercado Pago'
            self.fields['payment_reference'].widget.attrs.pop('pattern', None)
            self.fields['payment_reference'].widget.attrs.pop('inputmode', None)
            self.fields['payment_reference'].widget.attrs.pop('maxlength', None)
            self.fields['payment_reference'].widget.attrs.pop('minlength', None)
        

        # Ocultar el campo de direccion si no hay delivery
        if not self.delivery_available:
            self.fields['delivery_address'].widget = forms.HiddenInput()

    def clean_payment_reference(self):
        ref = self.cleaned_data.get('payment_reference', '').strip()
        if not ref:
            return ref

        # ===== MEXICO: alfanumerico, mas flexible =====
        if self.payment_region == 'MX':
            # Permitir alfanumerico, guiones, espacios
            if not re.match(r'^[A-Za-z0-9\- ]+$', ref):
                raise forms.ValidationError(
                    'La clave de rastreo solo puede contener letras, numeros, guiones y espacios.'
                )
            if len(ref) < 4:
                raise forms.ValidationError('La clave debe tener al menos 4 caracteres.')
            if len(ref) > 40:
                raise forms.ValidationError('La clave no puede tener mas de 40 caracteres.')
            return ref

        # ===== VENEZUELA: solo numeros 4-12 =====
        if not ref.isdigit():
            raise forms.ValidationError('La referencia solo puede contener numeros.')
        if len(ref) < 4:
            raise forms.ValidationError('La referencia debe tener al menos 4 digitos.')
        if len(ref) > 12:
            raise forms.ValidationError('La referencia no puede tener mas de 12 digitos.')
        return ref

    def clean_payment_proof(self):
        img = self.cleaned_data.get('payment_proof')
        # Solo validar si es un archivo NUEVO subido ahora
        from django.core.files.uploadedfile import UploadedFile
        if img and isinstance(img, UploadedFile) and img.size > 0:
            validate_image(img)
        return img

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get('shipping_method')
        address = (cleaned.get('delivery_address') or '').strip()

        # ===== VALIDACION DE SEGURIDAD =====
        # Verificar que el metodo elegido este disponible AHORA
        if method == 'delivery':
            if not self.delivery_available:
                raise forms.ValidationError(
                    '❌ Delivery no está disponible para este pedido. '
                    'El comercio está cerrado para delivery en este momento.'
                )
            if len(address) < 10:
                self.add_error(
                    'delivery_address',
                    'Ingresa una dirección más detallada (mínimo 10 caracteres).'
                )
        elif method == 'pickup':
            if not self.pickup_available:
                raise forms.ValidationError(
                    '❌ Retiro en tienda no está disponible para este pedido. '
                    'El comercio está cerrado en este momento.'
                )
            # Vaciar direccion si es pickup
            cleaned['delivery_address'] = ''
        else:
            raise forms.ValidationError(
                '❌ Método de entrega no válido.'
            )

        # ===== Validar el metodo de PAGO =====
        payment = cleaned.get('payment_method')
        if not payment:
            raise forms.ValidationError(
                '❌ Debes elegir un método de pago.'
            )

        if self.payment_region == 'MX':
            validos_mx = {
                'spei': self.accepts_spei,
                'mercadopago': self.accepts_mercadopago,
                'paypal': self.accepts_paypal,
            }
            if payment not in validos_mx:
                raise forms.ValidationError(
                    '❌ Método de pago no válido.'
                )
            if not validos_mx[payment]:
                raise forms.ValidationError(
                    '❌ Este comercio no acepta ese método de pago.'
                )
        else:
            if payment == 'transfer' and not self.accepts_transfer:
                raise forms.ValidationError(
                    '❌ Este comercio no acepta transferencia bancaria.'
                )
            if payment == 'mobile' and not self.accepts_mobile:
                raise forms.ValidationError(
                    '❌ Este comercio no acepta pago móvil.'
                )
            if payment not in ('transfer', 'mobile'):
                raise forms.ValidationError(
                    '❌ Método de pago no válido.'
                )

        return cleaned



# ============================================================
# FORMULARIOS DEL SISTEMA DE RECLAMOS
# ============================================================


class OrderClaimForm(forms.ModelForm):
    """Cliente abre un reclamo sobre un pedido."""

    class Meta:
        model = OrderClaim
        fields = ["claim_type", "description", "evidence"]
        widgets = {
            "claim_type": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Explica qué pasó con tu pedido (mínimo 20 caracteres).",
            }),
            "evidence": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
        }
        labels = {
            "claim_type": "¿Qué tipo de problema tuviste?",
            "description": "Describe el problema",
            "evidence": "Evidencia (opcional)",
        }
        help_texts = {
            "evidence": "Puedes adjuntar una captura de pantalla o foto (opcional).",
        }

    def clean_description(self):
        desc = (self.cleaned_data.get("description") or "").strip()
        if len(desc) < 20:
            raise forms.ValidationError("La descripción debe tener al menos 20 caracteres.")
        return desc

    def clean_evidence(self):
        img = self.cleaned_data.get("evidence")
        if img:
            from django.core.files.uploadedfile import UploadedFile
            if isinstance(img, UploadedFile) and img.size > 0:
                validate_image(img)
        return img


class OrderClaimMessageForm(forms.ModelForm):
    """Mensaje dentro de la conversación de un reclamo."""

    class Meta:
        model = OrderClaimMessage
        fields = ["message", "attachment"]
        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Escribe tu mensaje...",
            }),
            "attachment": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
        }
        labels = {
            "message": "Mensaje",
            "attachment": "Adjunto (opcional)",
        }

    def clean_message(self):
        msg = (self.cleaned_data.get("message") or "").strip()
        if len(msg) < 2:
            raise forms.ValidationError("El mensaje es muy corto.")
        return msg

    def clean_attachment(self):
        img = self.cleaned_data.get("attachment")
        if img:
            from django.core.files.uploadedfile import UploadedFile
            if isinstance(img, UploadedFile) and img.size > 0:
                validate_image(img)
        return img
