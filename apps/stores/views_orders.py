"""Vistas del dashboard para gestionar pedidos de un comercio."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView

from apps.notifications.email_service import send_order_item_rejected
from apps.notifications.models import notify
from apps.orders.models import Order, OrderItem
from apps.orders.services import reject_order_item

from .mixins import ManagerRequiredMixin, RoleContextMixin
from .models import Store, StoreUserPermission


# ============================================================
# Helpers
# ============================================================
def _check_store_manager(request, store):
    """True si el user puede gestionar items de este store."""
    if request.user.is_superuser:
        return True
    return StoreUserPermission.objects.filter(
        user=request.user, store=store, is_active=True,
        role__in=['owner', 'manager']
    ).exists()


def _update_order_status_after_item_change(order):
    """Si todos los items estan resueltos, actualiza el estado del Order."""
    statuses = set(order.items.values_list('status', flat=True))
    if 'pending' in statuses:
        return

    # Todos resueltos (o cancelados, o confirmados, o enviados)
    non_cancelled = statuses - {'cancelled'}
    if not non_cancelled:
        order.status = 'cancelled'
    elif all(s in ('shipped', 'delivered') for s in non_cancelled):
        order.status = 'shipped'
    else:
        order.status = 'confirmed'
    order.save(update_fields=['status'])


# ============================================================
# Vistas
# ============================================================
class StoreOrdersView(RoleContextMixin, ManagerRequiredMixin, ListView):
    """Lista de pedidos que contienen items de este comercio."""
    template_name = "stores/dashboard/orders.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        from django.db.models import Q
        store = self.get_store()
        status_filter = self.request.GET.get('status', 'pending')
        search = self.request.GET.get('q', '').strip()

        order_ids = OrderItem.objects.filter(store=store).values_list('order_id', flat=True).distinct()
        qs = Order.objects.filter(id__in=order_ids).prefetch_related('items__store')

        if status_filter == 'pending':
            qs = qs.filter(items__store=store, items__status='pending').distinct()
        elif status_filter == 'confirmed':
            qs = qs.filter(items__store=store, items__status='confirmed').distinct()
        elif status_filter == 'shipped':
            qs = qs.filter(
                items__store=store,
                items__status__in=['shipped', 'delivered']
            ).distinct()
        elif status_filter == 'cancelled':
            qs = qs.filter(items__store=store, items__status='cancelled').distinct()

        # Búsqueda por secuencia de caracteres (código, cliente, referencia)
        if search:
            qs = qs.filter(
                Q(reference_code__icontains=search) |
                Q(user__username__icontains=search) |
                Q(payment_reference__icontains=search)
            ).distinct()

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = self.get_store()
        context['store'] = store
        context['current_status'] = self.request.GET.get('status', 'pending')

        base = OrderItem.objects.filter(store=store)
        context['count_pending'] = base.filter(status='pending').count()
        context['count_confirmed'] = base.filter(status='confirmed').count()
        context['count_shipped'] = base.filter(status__in=['shipped', 'delivered']).count()
        context['count_cancelled'] = base.filter(status='cancelled').count()
        context['search'] = self.request.GET.get('q', '').strip()

        return context


class StoreOrderDetailView(RoleContextMixin, ManagerRequiredMixin, DetailView):
    """Detalle de un pedido. Solo muestra items de este comercio."""
    template_name = "stores/dashboard/order_detail.html"
    context_object_name = "order"
    pk_url_kwarg = "order_id"

    def get_queryset(self):
        store = self.get_store()
        order_ids = OrderItem.objects.filter(store=store).values_list('order_id', flat=True)
        return Order.objects.filter(id__in=order_ids).prefetch_related('items__product')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = self.get_store()
        context['store'] = store
        context['my_items'] = self.object.items.filter(store=store).select_related('product')
        # Otros items del pedido (de otras tiendas) — sin datos sensibles
        context['other_items_count'] = self.object.items.exclude(store=store).count()
        return context


# ============================================================
# Acciones (POST)
# ============================================================
@login_required(login_url='login')
def approve_order_item(request, store_id, order_id, item_id):
    if request.method != 'POST':
        return HttpResponseBadRequest("Metodo no permitido")

    store = get_object_or_404(Store, id=store_id)
    if not _check_store_manager(request, store):
        raise Http404()

    item = get_object_or_404(OrderItem, id=item_id, order_id=order_id, store=store)

    if item.status != 'pending':
        messages.warning(request, 'Este item ya fue procesado.')
        return redirect('stores:order_detail', store_id=store.id, order_id=order_id)

    item.status = 'confirmed'
    item.save(update_fields=['status'])
    _update_order_status_after_item_change(item.order)

    notify(
        item.order.user,
        'order_confirmed',
        f'Producto aprobado: {item.product_name}',
        f'Tu pedido {item.order.reference_code} fue aprobado por {store.name}. Pronto se enviará.',
        link=f'/orders/{item.order_id}/'
    )

    messages.success(request, f'Item "{item.product_name}" aprobado.')
    return redirect('stores:order_detail', store_id=store.id, order_id=order_id)


@login_required(login_url='login')
def reject_order_item_view(request, store_id, order_id, item_id):
    if request.method != 'POST':
        return HttpResponseBadRequest("Metodo no permitido")

    store = get_object_or_404(Store, id=store_id)
    if not _check_store_manager(request, store):
        raise Http404()

    item = get_object_or_404(OrderItem, id=item_id, order_id=order_id, store=store)

    if item.status == 'cancelled':
        messages.warning(request, 'Este item ya fue cancelado.')
        return redirect('stores:order_detail', store_id=store.id, order_id=order_id)

    if item.status in ('shipped', 'delivered'):
        messages.error(request, 'No puedes rechazar un item ya enviado.')
        return redirect('stores:order_detail', store_id=store.id, order_id=order_id)

    reject_order_item(item, reason=f'Rechazado por {request.user.username}')
    _update_order_status_after_item_change(item.order)

    notify(
        item.order.user,
        'order_rejected',
        f'Producto rechazado: {item.product_name}',
        f'{store.name} no pudo completar este item de tu pedido {item.order.reference_code}.',
        link=f'/orders/{item.order_id}/'
    )

    # Email al cliente (no bloquea si falla)
    send_order_item_rejected(
        order=item.order,
        item=item,
        store_name=store.name,
        request=request,
    )

    messages.success(request, f'Item "{item.product_name}" rechazado. Stock devuelto.')
    return redirect('stores:order_detail', store_id=store.id, order_id=order_id)


@login_required(login_url='login')
def mark_item_shipped(request, store_id, order_id, item_id):
    if request.method != 'POST':
        return HttpResponseBadRequest("Metodo no permitido")

    store = get_object_or_404(Store, id=store_id)
    if not _check_store_manager(request, store):
        raise Http404()

    item = get_object_or_404(OrderItem, id=item_id, order_id=order_id, store=store)

    if item.status != 'confirmed':
        messages.warning(request, 'Solo puedes enviar items previamente confirmados.')
        return redirect('stores:order_detail', store_id=store.id, order_id=order_id)

    item.status = 'shipped'
    item.save(update_fields=['status'])
    _update_order_status_after_item_change(item.order)

    notify(
        item.order.user,
        'order_shipped',
        f'Producto enviado: {item.product_name}',
        f'{store.name} envió tu pedido {item.order.reference_code}.',
        link=f'/orders/{item.order_id}/'
    )

    messages.success(request, f'Item "{item.product_name}" marcado como enviado.')
    return redirect('stores:order_detail', store_id=store.id, order_id=order_id)


@login_required(login_url="login")
def mark_item_delivered(request, store_id, order_id, item_id):
    """Marca un item como entregado al cliente."""
    if request.method != "POST":
        return HttpResponseBadRequest("Metodo no permitido")

    store = get_object_or_404(Store, id=store_id)
    if not _check_store_manager(request, store):
        raise Http404()

    item = get_object_or_404(OrderItem, id=item_id, order_id=order_id, store=store)

    # Permitir marcar entregado si:
    # - Esta confirmado Y el pedido es de retiro (pickup)
    # - O esta enviado (delivery)
    if item.status == "confirmed" and item.order.shipping_method != "pickup":
        messages.warning(request, "Debes marcar como enviado primero.")
        return redirect("stores:order_detail", store_id=store.id, order_id=order_id)

    if item.status not in ("confirmed", "shipped"):
        messages.warning(request, "Este item no puede marcarse como entregado.")
        return redirect("stores:order_detail", store_id=store.id, order_id=order_id)

    item.status = "delivered"
    item.save(update_fields=["status"])
    _update_order_status_after_item_change(item.order)

    notify(
        item.order.user,
        "order_completed",
        f"Producto entregado: {item.product_name}",
        f"{store.name} marco tu pedido {item.order.reference_code} como entregado.",
        link=f"/orders/{item.order_id}/"
    )

    messages.success(request, f'Item "{item.product_name}" marcado como entregado.')
    return redirect("stores:order_detail", store_id=store.id, order_id=order_id)
