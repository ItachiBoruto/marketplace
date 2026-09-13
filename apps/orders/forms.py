from django import forms

from .models import Order


class PaymentForm(forms.ModelForm):
    """Formulario donde el cliente reporta los datos de su pago."""

    class Meta:
        model = Order
        fields = ('payment_bank', 'payment_reference', 'payment_date', 'payment_proof', 'notes')
        widgets = {
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
            'payment_bank': 'Banco emisor',
            'payment_reference': 'Número de referencia',
            'payment_date': 'Fecha del pago',
            'payment_proof': 'Comprobante (imagen)',
            'notes': 'Notas (opcional)',
        }

    def clean_payment_reference(self):
        ref = self.cleaned_data.get('payment_reference', '').strip()
        if len(ref) < 4:
            raise forms.ValidationError('La referencia debe tener al menos 4 caracteres.')
        return ref