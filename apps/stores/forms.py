from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Store, UserProfile
from apps.products.models import Product


# ===== FORMULARIOS DE REGISTRO =====

class CustomUserCreationForm(UserCreationForm):
    """
    Formulario personalizado para el registro de usuarios.
    Incluye campos adicionales: email y teléfono.
    """
    email = forms.EmailField(
        required=True,
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        label="Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Crear el perfil con el teléfono
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data['phone']
            )
        return user


# ===== FORMULARIOS DEL DASHBOARD =====

class ProductForm(forms.ModelForm):
    """
    Formulario para crear/editar productos.
    """
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'additional_info', 'image', 'stock', 'keywords', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'additional_info': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nombre del producto',
            'price': 'Precio',
            'description': 'Descripción',
            'additional_info': 'Información adicional (ingredientes, nutricional, etc.)',
            'image': 'Imagen',
            'stock': 'Stock disponible',
            'keywords': 'Palabras clave (separadas por comas)',
            'is_available': 'Disponible',
        }


class StockAdjustForm(forms.ModelForm):
    """
    Formulario para ajustar el stock de un producto.
    """
    class Meta:
        model = Product
        fields = ['stock']
        labels = {'stock': 'Nuevo stock total'}
        help_texts = {'stock': 'Ingresa la cantidad total que deseas tener en inventario.'}
        widgets = {
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class StoreProfileForm(forms.ModelForm):
    """
    Formulario para editar el perfil del comercio.
    """
    class Meta:
        model = Store
        fields = ['name', 'logo', 'description', 'is_active', 'legal_name', 'rif', 'address', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rif': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nombre comercial',
            'logo': 'Logo',
            'description': 'Descripción',
            'is_active': '¿Activo?',
            'legal_name': 'Razón social',
            'rif': 'RIF',
            'address': 'Dirección',
            'phone': 'Teléfono (opcional)',
            'email': 'Correo electrónico (opcional)',
        }