from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    """Notificacion in-app para un usuario."""

    TYPE_CHOICES = [
        ("order_created", "Pedido creado"),
        ("order_confirmed", "Pedido confirmado"),
        ("order_shipped", "Pedido enviado"),
        ("order_rejected", "Pedido rechazado"),
        ("order_completed", "Pedido completado"),
        ("payment_confirmed", "Pago confirmado"),
        ("system", "Sistema"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default="system")
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "-created_at"]),
        ]
        verbose_name = "Notificacion"
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        return f"[{self.type}] {self.title} -> {self.user.username}"


# ============================================================
# Helpers
# ============================================================
def notify(user, ntype, title, message="", link=""):
    """Crea una notificacion para un usuario."""
    return Notification.objects.create(
        user=user, type=ntype, title=title, message=message, link=link
    )


def notify_superusers(ntype, title, message="", link=""):
    """Notifica a todos los superusers activos."""
    for u in User.objects.filter(is_superuser=True, is_active=True):
        notify(u, ntype, title, message, link)
