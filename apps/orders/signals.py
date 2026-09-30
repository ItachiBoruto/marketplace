# -*- coding: utf-8 -*-
"""
Signals de la app orders.

Auto-marca notificaciones relacionadas a un pedido cuando este
llega a un estado terminal (completed, cancelled, expired).
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.models import Notification

from .models import Order, OrderItem


ESTADOS_TERMINALES = ("completed", "cancelled", "expired")


@receiver(post_save, sender=Order)
def marcar_notificaciones_leidas_al_terminar(sender, instance, **kwargs):
    """
    Cuando un pedido llega a un estado terminal, marca como leidas
    TODAS las notificaciones sin leer relacionadas con ese pedido.

    Esto evita que se acumulen notificaciones tipo "Nuevo pedido X"
    que ya no requieren ninguna accion del usuario.
    """
    if instance.status not in ESTADOS_TERMINALES:
        return

    # Patrones de link que apuntan al pedido
    #   - Admin/owner/manager: /orders/panel/<pk>/
    #   - Cliente:              /orders/<pk>/
    patrones = [
        f"/orders/panel/{instance.pk}/",
        f"/orders/{instance.pk}/",
    ]

    # Marcar como leidas sin disparar post_save recursivo
    marcadas = 0
    for patron in patrones:
        actualizadas = Notification.objects.filter(
            is_read=False,
            link__endswith=patron,
        ).update(is_read=True)
        marcadas += actualizadas

    return marcadas


# ============================================================
# SINCRONIZACION Order <-> OrderItem
# ============================================================
# Mapeo autoritativo: order.status -> item.status esperado
MAPEO_ORDER_A_ITEM = {
    'pending_payment': 'pending',
    'payment_submitted': 'pending',
    'confirmed': 'confirmed',
    'shipped': 'shipped',
    'completed': 'delivered',
    'cancelled': 'cancelled',
    'expired': 'cancelled',
}


@receiver(post_save, sender=OrderItem)
def sincronizar_order_con_items(sender, instance, **kwargs):
    """
    Cuando se guarda un OrderItem, recalcula el status del Order padre.

    Reglas:
    - Si hay algun item pending -> order queda como esta (no tocar)
    - Si todos son cancelled -> order = cancelled
    - Si todos son delivered -> order = completed
    - Si todos son shipped/delivered -> order = shipped
    - Resto -> order = confirmed
    """
    order = instance.order
    statuses = set(order.items.values_list('status', flat=True))

    if 'pending' in statuses:
        return

    non_cancelled = statuses - {'cancelled'}

    if not non_cancelled:
        target = 'cancelled'
    elif all(s == 'delivered' for s in non_cancelled):
        target = 'completed'
    elif all(s in ('shipped', 'delivered') for s in non_cancelled):
        target = 'shipped'
    else:
        target = 'confirmed'

    if order.status != target:
        order.status = target
        order.save(update_fields=['status'])
