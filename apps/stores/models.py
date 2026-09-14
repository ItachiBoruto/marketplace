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
