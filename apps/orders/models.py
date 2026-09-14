from django.contrib.auth.models import User
from django.db import models

from apps.products.models import Product
from apps.stores.models import Store


class Order(models.Model):
    """Pedido único del usuario. Puede contener items de varios comercios."""

    STATUS_CHOICES = [
        ('pending_payment', 'Esperando pago'),
        ('payment_submitted', 'Pago reportado'),
        ('confirmed', 'Pago confirmado'),
        ('shipped', 'Enviado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('expired', 'Reserva expirada'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='orders',
        verbose_name='Cliente'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending_payment',
        verbose_name='Estado'
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Total')
    exchange_rate = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        verbose_name='Tasa BCV al momento del pedido'
    )

    # Datos del pago (los llena el usuario)
    payment_bank = models.CharField(max_length=100, blank=True, verbose_name='Banco emisor')
    payment_reference = models.CharField(max_length=50, blank=True, verbose_name='Referencia')
    payment_proof = models.ImageField(
        upload_to='orders/proofs/', blank=True, null=True,
        verbose_name='Comprobante'
    )
    payment_date = models.DateField(null=True, blank=True, verbose_name='Fecha del pago')

    notes = models.TextField(blank=True, verbose_name='Notas del cliente')

    # ===== Reserva de stock =====
    reservation_expires_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Reserva vence el'
    )
    stock_released = models.BooleanField(
        default=False, verbose_name='Stock liberado'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f"Pedido #{self.pk} - {self.user.username} (${self.total})"

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def is_reservation_active(self):
        """True si la reserva sigue activa (no expirada y no liberada)."""
        from django.utils import timezone
        if self.stock_released:
            return False
        if not self.reservation_expires_at:
            return False
        return timezone.now() < self.reservation_expires_at

    def minutes_until_expiry(self):
        """Devuelve los minutos restantes de la reserva (0 si expiró)."""
        from django.utils import timezone
        if not self.reservation_expires_at:
            return 0
        delta = self.reservation_expires_at - timezone.now()
        return max(0, int(delta.total_seconds() // 60))


class OrderItem(models.Model):
    """Item individual de un pedido. Cada item pertenece a un comercio."""

    ITEM_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Producto'
    )
    store = models.ForeignKey(
        Store, on_delete=models.PROTECT, related_name='order_items',
        verbose_name='Comercio'
    )

    # Datos congelados al momento de la compra (por si el producto cambia después)
    product_name = models.CharField(max_length=200, verbose_name='Nombre del producto')
    product_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Cantidad')

    # Estado por item (para que cada vendedor gestione el suyo)
    status = models.CharField(
        max_length=20, choices=ITEM_STATUS_CHOICES, default='pending',
        verbose_name='Estado del item'
    )

    class Meta:
        verbose_name = 'Item del pedido'
        verbose_name_plural = 'Items del pedido'

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    def get_subtotal(self):
        return self.product_price * self.quantity


class ExchangeRate(models.Model):
    """Tasa de cambio USD -> Bs del BCV (automatica o manual)."""

    FUENTE_CHOICES = [
        ('AUTO', 'Automatica (BCV)'),
        ('MANUAL', 'Manual'),
    ]

    fecha = models.DateField(verbose_name='Fecha')
    valor = models.DecimalField(max_digits=12, decimal_places=4, verbose_name='Bs por USD')
    fuente = models.CharField(
        max_length=10, choices=FUENTE_CHOICES, default='AUTO',
        verbose_name='Fuente'
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='Usar esta tasa',
        help_text='Si esta activa, esta tasa se usara hasta que crees otra o la desactives.'
    )
    notas = models.CharField(max_length=200, blank=True, verbose_name='Notas')
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha', '-actualizado_en']
        verbose_name = 'Tasa de cambio'
        verbose_name_plural = 'Tasas de cambio'

    def __str__(self):
        return f"{self.fecha} | {self.valor} Bs/USD | {self.get_fuente_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            ExchangeRate.objects.exclude(pk=self.pk).update(is_active=False)
