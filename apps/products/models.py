from django.db import models
from apps.stores.models import Store

class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
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