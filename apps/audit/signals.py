from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.inventory.models import StockMovement
from apps.products.models import Product
from apps.stores.models import Store, StoreUserPermission

from .services import log_action


# ========== Product ==========
@receiver(post_save, sender=Product)
def log_product_save(sender, instance, created, **kwargs):
    if created:
        log_action(
            action="create",
            details=f"Producto creado: {instance.name} (ID {instance.pk})",
            store=instance.store,
        )
    else:
        log_action(
            action="update",
            details=f"Producto actualizado: {instance.name} (ID {instance.pk})",
            store=instance.store,
        )


@receiver(post_delete, sender=Product)
def log_product_delete(sender, instance, **kwargs):
    log_action(
        action="delete",
        details=f"Producto eliminado: {instance.name} (ID {instance.pk})",
        store=instance.store,
    )


# ========== StockMovement ==========
@receiver(post_save, sender=StockMovement)
def log_stock_movement(sender, instance, created, **kwargs):
    if created:
        log_action(
            action="stock_adjust",
            details=(
                f"Movimiento de stock: {instance.product.name} "
                f"(cambio: {instance.quantity_change:+d})"
            ),
            store=instance.store,
        )


# ========== Store ==========
@receiver(post_save, sender=Store)
def log_store_save(sender, instance, created, **kwargs):
    if not created:
        log_action(
            action="update",
            details=f"Comercio actualizado: {instance.name} (ID {instance.pk})",
            store=instance,
        )


# ========== StoreUserPermission ==========
@receiver(post_save, sender=StoreUserPermission)
def log_permission_save(sender, instance, created, **kwargs):
    verb = "otorgado" if created else "actualizado"
    log_action(
        action="permission_change",
        details=(
            f"Permiso {verb}: {instance.user.username} "
            f"como {instance.get_role_display()} en {instance.store.name}"
        ),
        store=instance.store,
    )


@receiver(post_delete, sender=StoreUserPermission)
def log_permission_delete(sender, instance, **kwargs):
    log_action(
        action="permission_change",
        details=(
            f"Permiso revocado: {instance.user.username} "
            f"en {instance.store.name}"
        ),
        store=instance.store,
    )


# ============================================================
# LOGINS (exitosos y fallidos)
# ============================================================
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registra un login exitoso."""
    log_action(
        action="login",
        details=f"Login exitoso desde {get_client_ip(request)}",
        user=user,
        ip_address=get_client_ip(request),
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request=None, **kwargs):
    """Registra un intento de login fallido."""
    username = credentials.get("username", "desconocido")
    ip = get_client_ip(request) if request else None

    # Buscar si el usuario existe (para asociar el registro)
    from django.contrib.auth.models import User
    target_user = None
    try:
        target_user = User.objects.filter(username__iexact=username).first()
        if not target_user:
            target_user = User.objects.filter(email__iexact=username).first()
    except Exception:
        pass

    log_action(
        action="login_failed",
        details=f"Intento de login fallido con: {username}",
        user=target_user,
        ip_address=ip,
    )


def get_client_ip(request):
    """Extrae la IP del request (con soporte para proxies)."""
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
