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
