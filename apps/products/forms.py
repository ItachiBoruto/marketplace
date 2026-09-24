from django import forms
from django.core.files.uploadedfile import UploadedFile

from apps.utils.validators import validate_image

from .models import Category, Product


class ProductForm(forms.ModelForm):
    """Formulario para crear/editar productos."""

    class Meta:
        model = Product
        fields = [
            "category", "name", "price", "description", "additional_info",
            "image", "stock", "keywords", "is_available",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "additional_info": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "keywords": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "name": "Nombre del producto",
            "category": "Categoria",
            "price": "Precio",
            "description": "Descripción",
            "additional_info": "Información adicional (ingredientes, nutricional, etc.)",
            "image": "Imagen",
            "stock": "Stock disponible",
            "keywords": "Palabras clave (separadas por comas)",
            "is_available": "Disponible",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        self.fields["category"].empty_label = "-- Sin categoria --"
        self.fields["category"].required = False

    def clean_image(self):
        img = self.cleaned_data.get('image')
        # Solo validar si es un archivo NUEVO subido ahora.
        # Los archivos existentes (de Cloudinary u otro storage)
        # no son UploadedFile y no tienen extension en el name.
        if img and isinstance(img, UploadedFile):
            if img.size > 0:
                validate_image(img)
        return img
