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
