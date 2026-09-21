from django.db import models
from django.contrib.auth.models import User

class Store(models.Model):
    legal_name = models.CharField(max_length=200, verbose_name="Razón social")
    rif = models.CharField(max_length=20, unique=True, verbose_name="RIF")
    address = models.TextField(blank=True, verbose_name="Dirección")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")
    name = models.CharField(max_length=200, verbose_name="Nombre comercial")
    logo = models.ImageField(upload_to='stores/logos/', blank=True, null=True, verbose_name="Logo")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="¿Activo?")

    # ===== Delivery =====
    offers_delivery = models.BooleanField(
        default=False,
        verbose_name="¿Ofrece delivery?",
        help_text="Activa para permitir a los clientes pedir envío a domicilio."
    )
    delivery_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Tarifa de delivery",
        help_text="Monto en dólares que se cobrará por el envío."
    )

    # ===== Datos bancarios (para pagos directos al comercio) =====
    bank_name = models.CharField(
        max_length=100, blank=True,
        verbose_name="Banco",
        help_text="Ej: Banco de Venezuela, Banesco, Mercantil..."
    )
    account_number = models.CharField(
        max_length=40, blank=True,
        verbose_name="Número de cuenta",
        help_text="Ej: 0102-1234-56-78901234"
    )
    account_holder = models.CharField(
        max_length=150, blank=True,
        verbose_name="Titular de la cuenta"
    )
    document = models.CharField(
        max_length=20, blank=True,
        verbose_name="Cédula o RIF",
        help_text="Ej: V-12345678 o J-12345678-9"
    )
    payment_phone = models.CharField(
        max_length=20, blank=True,
        verbose_name="Teléfono para pago móvil",
        help_text="Ej: 0414-1234567 (opcional, si acepta pago móvil)"
    )
    payment_email = models.EmailField(
        blank=True,
        verbose_name="Email para notificar pagos",
        help_text="A dónde te llegan las notificaciones de transferencias (opcional)"
    )
    payment_notes = models.TextField(
        blank=True,
        verbose_name="Notas adicionales",
        help_text="Información extra para el cliente (opcional)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    users = models.ManyToManyField(
        User,
        through='StoreUserPermission',
        related_name='stores',
        blank=True
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Comercio"
        verbose_name_plural = "Comercios"


class StoreUserPermission(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Propietario'),
        ('manager', 'Gestor/Moderador'),
        ('viewer', 'Visualizador'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_permissions')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='user_permissions')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='manager')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'store')
        verbose_name = "Permiso de usuario"
        verbose_name_plural = "Permisos de usuarios"
    
    def __str__(self):
        return f"{self.user.username} - {self.store.name} ({self.get_role_display()})"


class StorePaymentChangeRequest(models.Model):
    """
    Solicitud de cambio de datos bancarios de un comercio.
    Requiere doble autorizacion: owner solicita + superuser aprueba.
    """

    STATUS_CHOICES = [
        ('pending', 'Pendiente de aprobación'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
    ]

    store = models.ForeignKey(
        Store, on_delete=models.CASCADE,
        related_name='payment_change_requests',
        verbose_name='Comercio'
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='payment_requests_made',
        verbose_name='Solicitado por'
    )

    # Valores propuestos
    new_bank_name = models.CharField(max_length=100, blank=True, verbose_name='Banco (nuevo)')
    new_account_number = models.CharField(max_length=40, blank=True, verbose_name='Cuenta (nueva)')
    new_account_holder = models.CharField(max_length=150, blank=True, verbose_name='Titular (nuevo)')
    new_document = models.CharField(max_length=20, blank=True, verbose_name='Cédula/RIF (nuevo)')
    new_payment_phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono (nuevo)')

    # Snapshot del estado actual (para comparar)
    old_bank_name = models.CharField(max_length=100, blank=True)
    old_account_number = models.CharField(max_length=40, blank=True)
    old_account_holder = models.CharField(max_length=150, blank=True)
    old_document = models.CharField(max_length=20, blank=True)
    old_payment_phone = models.CharField(max_length=20, blank=True)

    reason = models.TextField(blank=True, verbose_name='Motivo del cambio')

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        verbose_name='Estado'
    )
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='payment_requests_reviewed',
        verbose_name='Revisado por'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, verbose_name='Motivo del rechazo')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitud de cambio de datos bancarios'
        verbose_name_plural = 'Solicitudes de cambio de datos bancarios'
        indexes = [
            models.Index(fields=['store', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Solicitud #{self.pk} - {self.store.name} ({self.get_status_display()})"

    def has_changes(self):
        """True si al menos un campo propuesto difiere del actual."""
        return any([
            self.new_bank_name != self.old_bank_name,
            self.new_account_number != self.old_account_number,
            self.new_account_holder != self.old_account_holder,
            self.new_document != self.old_document,
            self.new_payment_phone != self.old_payment_phone,
        ])


class StoreSchedule(models.Model):
    """Horario de atencion por dia de la semana para un comercio.

    Si el comercio no tiene horarios configurados, se asume ABIERTO 24/7
    (comportamiento por defecto para no romper comercios sin configurar).
    """

    DAY_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    store = models.ForeignKey(
        Store, on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='Comercio'
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=DAY_CHOICES,
        verbose_name='Día'
    )
    is_closed = models.BooleanField(
        default=False,
        verbose_name='Cerrado este día'
    )

    # Horario de retiro en tienda
    pickup_open = models.TimeField(null=True, blank=True, verbose_name='Retiro: abre')
    pickup_close = models.TimeField(null=True, blank=True, verbose_name='Retiro: cierra')

    # Horario de delivery
    delivery_open = models.TimeField(null=True, blank=True, verbose_name='Delivery: abre')
    delivery_close = models.TimeField(null=True, blank=True, verbose_name='Delivery: cierra')

    class Meta:
        unique_together = ('store', 'day_of_week')
        ordering = ['day_of_week']
        verbose_name = 'Horario del comercio'
        verbose_name_plural = 'Horarios del comercio'

    def __str__(self):
        day_name = self.get_day_of_week_display()
        if self.is_closed:
            return f"{self.store.name} - {day_name}: Cerrado"
        return f"{self.store.name} - {day_name}"

    def pickup_range(self):
        """Devuelve '08:00 - 20:00' o 'Cerrado' o '--'."""
        if self.is_closed:
            return 'Cerrado'
        if self.pickup_open and self.pickup_close:
            return f"{self.pickup_open.strftime('%H:%M')} - {self.pickup_close.strftime('%H:%M')}"
        return '--'

    def delivery_range(self):
        """Devuelve '08:00 - 20:00' o 'Cerrado' o '--'."""
        if self.is_closed:
            return 'Cerrado'
        if self.delivery_open and self.delivery_close:
            return f"{self.delivery_open.strftime('%H:%M')} - {self.delivery_close.strftime('%H:%M')}"
        return '--'
