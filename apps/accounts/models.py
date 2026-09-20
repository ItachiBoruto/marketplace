from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")

    # ===== Verificación de email =====
    email_verified = models.BooleanField(
        default=False,
        verbose_name="Email verificado"
    )
    email_verified_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Verificado el"
    )
    last_verification_sent_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Último envío de verificación"
    )
    verification_attempts_today = models.PositiveIntegerField(
        default=0,
        verbose_name="Reenvíos hoy"
    )
    verification_attempts_date = models.DateField(
        null=True, blank=True,
        verbose_name="Fecha de reenvíos"
    )

    # ===== Aceptacion de terminos y privacidad =====
    terms_accepted = models.BooleanField(
        default=False,
        verbose_name="Acepto Términos y Privacidad"
    )
    terms_accepted_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Aceptado el"
    )
    terms_version = models.CharField(
        max_length=20, blank=True,
        verbose_name="Versión de términos"
    )

    class Meta:
        db_table = "stores_userprofile"
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"{self.user.username} - {self.phone or 'Sin teléfono'}"
