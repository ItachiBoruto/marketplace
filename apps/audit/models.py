from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Creación"),
        ("update", "Actualización"),
        ("delete", "Eliminación"),
        ("stock_adjust", "Ajuste de stock"),
        ("permission_change", "Cambio de permisos"),
        ("login", "Inicio de sesión"),
        ("logout", "Cierre de sesión"),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True
    )
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stores_auditlog"
        ordering = ["-timestamp"]
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
