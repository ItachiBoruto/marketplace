from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    """Formulario para crear/editar productos."""

    class Meta:
        model = Product
        fields = [
            "name", "price", "description", "additional_info",
            "image", "stock", "keywords", "is_available",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "additional_info": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
            "keywords": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "name": "Nombre del producto",
            "price": "Precio",
            "description": "Descripción",
            "additional_info": "Información adicional (ingredientes, nutricional, etc.)",
            "image": "Imagen",
            "stock": "Stock disponible",
            "keywords": "Palabras clave (separadas por comas)",
            "is_available": "Disponible",
        }
