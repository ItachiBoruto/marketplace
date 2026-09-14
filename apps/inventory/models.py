from django.db import models
from apps.stores.models import Store
from apps.products.models import Product

class StockMovement(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, verbose_name="Comercio")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements', verbose_name="Producto")
    quantity_change = models.IntegerField(verbose_name="Cantidad (+/-)")

    MOVEMENT_CHOICES = [
        ('INIT', 'Carga inicial'),
        ('REST', 'Reposición'),
        ('SALE', 'Venta'),
        ('RETURN', 'Devolución'),
        ('ADJ', 'Ajuste manual'),
    ]
    movement_type = models.CharField(max_length=8, choices=MOVEMENT_CHOICES, verbose_name="Tipo de movimiento")
    created_by = models.CharField(max_length=100, blank=True, verbose_name="Responsable")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora")
    order_reference = models.CharField(max_length=50, blank=True, null=True, verbose_name="Referencia de pedido")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"

    def __str__(self):
        return f"{self.store.name} - {self.product.name}: {self.quantity_change}"