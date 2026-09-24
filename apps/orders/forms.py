from django import forms

from apps.utils.validators import validate_image

from .models import Order


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
                'placeholder': 'Número de referencia del pago'
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

        # ===== Choices de metodo de PAGO =====
        payment_choices = []
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

        # Ocultar el campo de direccion si no hay delivery
        if not self.delivery_available:
            self.fields['delivery_address'].widget = forms.HiddenInput()

    def clean_payment_reference(self):
        ref = self.cleaned_data.get('payment_reference', '').strip()
        if len(ref) < 4:
            raise forms.ValidationError('La referencia debe tener al menos 4 caracteres.')
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
        if payment == 'transfer' and not self.accepts_transfer:
            raise forms.ValidationError(
                '❌ Este comercio no acepta transferencia bancaria.'
            )
        if payment == 'mobile' and not self.accepts_mobile:
            raise forms.ValidationError(
                '❌ Este comercio no acepta pago móvil.'
            )
        if not payment:
            raise forms.ValidationError(
                '❌ Debes elegir un método de pago.'
            )

        return cleaned
