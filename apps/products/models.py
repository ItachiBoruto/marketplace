from django.db import models
from apps.stores.models import Store

class Category(models.Model):
    """Categoria de productos (alimentos, ferreteria, papeleria, etc.)."""
    name = models.CharField(max_length=80, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=80, unique=True, verbose_name="Slug (URL)")
    emoji = models.CharField(
        max_length=8, blank=True, default="",
        verbose_name="Emoji",
        help_text="Se muestra si no hay imagen"
    )
    image = models.ImageField(
        upload_to="categories/", blank=True, null=True,
        verbose_name="Imagen de fondo",
        help_text="Foto que aparece en la tarjeta del modal"
    )
    color = models.CharField(
        max_length=7, default="#e94560",
        verbose_name="Color de fondo",
        help_text="Color en hex (ej: #e94560) si no hay imagen"
    )
    order = models.PositiveSmallIntegerField(
        default=0, verbose_name="Orden",
        help_text="Menor numero aparece primero"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return f"{self.emoji} {self.name}".strip()


class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products',
        verbose_name='Categoria'
    )
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    additional_info = models.TextField(blank=True)
    image = models.ImageField(upload_to='', blank=True, null=True)  # SIN CARPETA
    stock = models.IntegerField(default=0)
    keywords = models.CharField(max_length=500, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.store.name} - {self.name}"