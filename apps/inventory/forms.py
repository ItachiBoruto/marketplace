from django import forms

from apps.products.models import Product


class StockAdjustForm(forms.ModelForm):
    """Formulario para ajustar el stock de un producto."""

    class Meta:
        model = Product
        fields = ["stock"]
        labels = {"stock": "Nuevo stock total"}
        help_texts = {"stock": "Ingresa la cantidad total que deseas tener en inventario."}
        widgets = {
            "stock": forms.NumberInput(attrs={"class": "form-control"}),
        }
