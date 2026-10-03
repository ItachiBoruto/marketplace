from django.contrib.auth.models import User
from django.db import models

from apps.products.models import Product
from apps.stores.models import Store


class Order(models.Model):
    """Pedido único del usuario. Puede contener items de varios comercios."""

    STATUS_CHOICES = [
        ('pending_payment', 'Esperando pago'),
        ('payment_submitted', 'Por verificar pago'),
        ('confirmed', 'Por entregar'),
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

    # ===== Envío =====
    SHIPPING_CHOICES = [
        ('pickup', 'Retiro en tienda'),
        ('delivery', 'Delivery a domicilio'),
    ]
    shipping_method = models.CharField(
        max_length=10, choices=SHIPPING_CHOICES, default='pickup',
        verbose_name='Método de entrega'
    )
    shipping_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Costo de envío'
    )
    delivery_address = models.TextField(
        blank=True,
        verbose_name='Dirección de entrega',
        help_text='Solo aplica cuando el método es delivery.'
    )

    # Datos del pago (los llena el usuario)
    PAYMENT_METHOD_CHOICES = [
        # Venezuela
        ('transfer', 'Transferencia bancaria'),
        ('mobile', 'Pago movil'),
        # Mexico
        ('spei', 'Transferencia SPEI'),
        ('mercadopago', 'Mercado Pago'),
        ('paypal', 'PayPal'),
    ]
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        default='',
        verbose_name='Metodo de pago'
    )
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

    # Codigo publico visible al usuario (diferente del pk interno)
    reference_code = models.CharField(
        max_length=20, unique=True, blank=True, null=True,
        verbose_name='Código de pedido',
        help_text='Se genera automáticamente. Ej: ORD-2609-A7B3'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def _generate_reference_code(self):
        """Genera un codigo unico tipo ORD-2609-A7B3."""
        import secrets
        import string
        from django.utils import timezone

        now = timezone.now()
        for _ in range(10):
            suffix = ''.join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(4)
            )
            code = f"ORD-{now.strftime('%y%m')}-{suffix}"
            if not Order.objects.filter(reference_code=code).exists():
                return code
        raise ValueError('No se pudo generar un codigo unico para el pedido')

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = self._generate_reference_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.reference_code or self.pk} - {self.user.username} (${self.total})"

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        """Suma de productos (sin envío)."""
        return self.total

    @property
    def grand_total(self):
        """Total con envío incluido."""
        from decimal import Decimal
        return (self.total or Decimal('0')) + (self.shipping_fee or Decimal('0'))

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


# ============================================================
# SISTEMA DE RECLAMOS
# ============================================================


class OrderClaim(models.Model):
    """
    Reclamo formal de un cliente sobre un pedido.

    Un pedido puede tener a lo sumo UN reclamo activo.
    Si el cliente quiere reportar otro problema, debe esperar a que
    el anterior se cierre.
    """

    CLAIM_TYPE_CHOICES = [
        ('no_received', 'No recibí el producto'),
        ('wrong_product', 'Recibí un producto distinto'),
        ('paid_more', 'Pagué de más por error'),
        ('paid_less', 'Pagué de menos / referencia mal anotada'),
        ('not_confirmed', 'El comercio no confirmó mi pago'),
        ('other', 'Otro problema'),
    ]

    STATUS_CHOICES = [
        ('open', 'Abierto'),
        ('in_review', 'En revisión por el comercio'),
        ('resolved', 'Resuelto por el comercio'),
        ('closed', 'Cerrado'),
        ('escalated', 'Escalado al administrador'),
        ('rejected', 'Rechazado por el administrador'),
    ]

    # ===== Relación con el pedido =====
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE,
        related_name='claim',
        verbose_name='Pedido',
    )
    opened_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='claims_opened',
        verbose_name='Abierto por',
    )

    # ===== Contenido del reclamo =====
    claim_type = models.CharField(
        max_length=20, choices=CLAIM_TYPE_CHOICES,
        verbose_name='Tipo de problema',
    )
    description = models.TextField(
        verbose_name='Descripción del problema',
        help_text='Explica qué pasó con el pedido.',
    )
    evidence = models.ImageField(
        upload_to='claims/evidence/', blank=True, null=True,
        verbose_name='Evidencia (imagen)',
        help_text='Comprobante, captura de pantalla, foto del producto, etc.',
    )

    # ===== Estado y resolución =====
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='open',
        verbose_name='Estado',
    )
    resolution = models.TextField(
        blank=True,
        verbose_name='Resolución',
        help_text='Cómo el comercio resolvió el reclamo.',
    )
    resolution_evidence = models.ImageField(
        upload_to='claims/resolutions/', blank=True, null=True,
        verbose_name='Evidencia de resolución (imagen)',
    )

    # ===== Quién y cuándo =====
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='claims_resolved',
        verbose_name='Resuelto por',
    )
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Resuelto el')

    escalated_at = models.DateTimeField(null=True, blank=True, verbose_name='Escalado el')
    escalated_reason = models.TextField(blank=True, verbose_name='Motivo del escalado')

    closed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='claims_closed',
        verbose_name='Cerrado por',
    )
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Cerrado el')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Reclamo'
        verbose_name_plural = 'Reclamos'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['opened_by', '-created_at']),
        ]

    def __str__(self):
        return f"Reclamo #{self.pk} - {self.order.reference_code} ({self.get_status_display()})"

    @property
    def is_active(self):
        """El reclamo sigue en curso (no cerrado ni rechazado)."""
        return self.status in ('open', 'in_review', 'resolved', 'escalated')


class OrderClaimMessage(models.Model):
    """
    Mensaje dentro de la conversación de un reclamo.
    Permite chat entre cliente y comercio, con adjuntos opcionales.
    """

    claim = models.ForeignKey(
        OrderClaim, on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Reclamo',
    )
    sender = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='claim_messages',
        verbose_name='Remitente',
    )
    message = models.TextField(
        verbose_name='Mensaje',
    )
    attachment = models.ImageField(
        upload_to='claims/attachments/', blank=True, null=True,
        verbose_name='Adjunto (imagen)',
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name='Mensaje del sistema',
        help_text='Mensajes automáticos (ej: "reclamo abierto", "escalado a admin").',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Mensaje de reclamo'
        verbose_name_plural = 'Mensajes de reclamo'
        indexes = [
            models.Index(fields=['claim', 'created_at']),
        ]

    def __str__(self):
        tipo = 'sistema' if self.is_system else self.sender.username
        return f"{self.claim_id} - {tipo} - {self.created_at:%d/%m %H:%M}"
