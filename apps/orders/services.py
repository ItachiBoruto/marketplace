from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.inventory.models import StockMovement
from apps.products.models import Product

from apps.notifications.email_service import send_new_order_to_admin
from apps.notifications.models import notify, notify_superusers

from .exchange import get_bcv_rate
from .models import Order, OrderItem


class InsufficientStockError(Exception):
    """Se lanza cuando un producto no tiene stock suficiente."""
    def __init__(self, product_name, requested, available):
        self.product_name = product_name
        self.requested = requested
        self.available = available
        super().__init__(
            f'"{product_name}" no tiene stock suficiente. '
            f'Pediste {requested}, disponible {available}.'
        )


class EmptyCartError(Exception):
    """El carrito está vacío."""
    pass


@transaction.atomic
def create_order_from_cart(user, payment_data, cart, store=None):
    """
    Crea un pedido desde el carrito con reserva atómica de stock.

    Si se pasa `store`, solo procesa los items de ese comercio.
    Si no, procesa todos los items del carrito.

    Bloquea las filas de los productos durante la transacción, valida stock,
    descuenta, crea OrderItems y StockMovements, y vacía solo esos items.
    """
    qs = cart.items.select_related('product', 'product__store').all()
    if store is not None:
        qs = qs.filter(product__store=store)

    items = list(qs)
    if not items:
        raise EmptyCartError('No hay productos para procesar.')

    product_ids = [item.product_id for item in items]

    # Bloqueo de filas: nadie más puede leer/escribir hasta que termines
    locked_products = {
        p.id: p
        for p in Product.objects.select_for_update().filter(id__in=product_ids)
    }

    # Validar stock con las filas bloqueadas
    for item in items:
        product = locked_products[item.product_id]
        if item.quantity > product.stock:
            raise InsufficientStockError(
                product.name, item.quantity, product.stock
            )

    # Crear el pedido con reserva activa
    now = timezone.now()
    reservation_minutes = getattr(settings, 'ORDER_RESERVATION_MINUTES', 30)

    rate = get_bcv_rate()

    order = Order.objects.create(
        user=user,
        total=cart.get_total(),
        exchange_rate=rate,
        status='payment_submitted',
        reservation_expires_at=now + timedelta(minutes=reservation_minutes),
        **payment_data
    )

    # Crear items + descontar stock + registrar movimientos
    for item in items:
        product = locked_products[item.product_id]

        OrderItem.objects.create(
            order=order,
            product=product,
            store=product.store,
            product_name=product.name,
            product_price=item.price,
            quantity=item.quantity,
        )

        product.stock -= item.quantity
        product.save(update_fields=['stock'])

        StockMovement.objects.create(
            store=product.store,
            product=product,
            quantity_change=-item.quantity,
            movement_type='SALE',
            created_by=user.username,
            order_reference=f'Pedido #{order.pk}',
        )

    # Vaciar SOLO los items procesados
    for item in items:
        item.delete()

    # ===== Notificaciones =====
    # Al admin (superusers): nuevo pedido recibido
    notify_superusers(
        "order_created",
        f"Nuevo pedido {order.reference_code}",
        f"{user.username} hizo un pedido por ${order.total}.",
        link=f"/admin/orders/order/{order.pk}/change/"
    )

    # Al cliente: pedido registrado
    notify(
        user,
        "order_created",
        f"Pedido {order.reference_code} registrado",
        "Estamos verificando tu pago. Te avisaremos cuando se confirme.",
        link=f"/orders/{order.pk}/"
    )

    # Email al admin (no bloquea si falla)
    send_new_order_to_admin(order)

    return order


@transaction.atomic
def release_order_stock(order, reason='Liberación manual'):
    """
    Devuelve el stock de un pedido al inventario.
    Idempotente: si ya se liberó, no hace nada.
    """
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.stock_released:
        return False

    for item in order.items.select_related('product', 'store'):
        if item.product_id is None:
            continue
        product = Product.objects.select_for_update().get(pk=item.product_id)
        product.stock += item.quantity
        product.save(update_fields=['stock'])

        StockMovement.objects.create(
            store=item.store,
            product=product,
            quantity_change=item.quantity,
            movement_type='RETURN',
            created_by='system',
            order_reference=f'{reason} - Pedido #{order.pk}',
        )

    order.stock_released = True
    order.save(update_fields=['stock_released'])
    return True


@transaction.atomic
def reject_order_item(item, reason='Rechazado por el vendedor'):
    """
    Rechaza un item específico: devuelve su stock.
    """
    item = OrderItem.objects.select_for_update().select_related(
        'product', 'store'
    ).get(pk=item.pk)

    if item.status == 'cancelled':
        return False

    if item.product_id is not None:
        product = Product.objects.select_for_update().get(pk=item.product_id)
        product.stock += item.quantity
        product.save(update_fields=['stock'])

        StockMovement.objects.create(
            store=item.store,
            product=product,
            quantity_change=item.quantity,
            movement_type='RETURN',
            created_by='system',
            order_reference=f'{reason} - Pedido #{item.order_id}',
        )

    item.status = 'cancelled'
    item.save(update_fields=['status'])
    return True


def expire_old_reservations():
    """
    Libera el stock de pedidos cuya reserva expiró.
    Devuelve el número de pedidos expirados.
    """
    now = timezone.now()
    expired = Order.objects.filter(
        status='payment_submitted',
        stock_released=False,
        reservation_expires_at__lt=now,
    )
    count = 0
    for order in expired:
        try:
            release_order_stock(order, reason='Reserva expirada')
            order.status = 'expired'
            order.save(update_fields=['status'])
            count += 1
        except Exception:
            continue
    return count
