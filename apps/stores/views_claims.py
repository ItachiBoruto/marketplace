# -*- coding: utf-8 -*-
"""
Vistas de reclamos del lado del COMERCIO.

El comercio puede:
- Ver el detalle del reclamo + chat
- Responder al cliente
- Marcar como resuelto (con resolución + evidencia)
- Escalar al superuser
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from django.utils import timezone

from apps.notifications.models import notify
from apps.orders.forms import OrderClaimMessageForm
from apps.orders.models import Order, OrderClaim, OrderClaimMessage
from apps.utils.async_tasks import run_async

from .mixins import ManagerRequiredMixin, RoleContextMixin
from .models import Store


ESTADOS_CERRADOS = ('closed', 'rejected')


def _check_store_manager(request, store):
    """El usuario logueado puede gestionar este comercio?"""
    if not request.user.is_authenticated:
        return False
    if request.user.is_superuser:
        return True
    from apps.stores.models import StoreUserPermission
    return StoreUserPermission.objects.filter(
        store=store, user=request.user, is_active=True,
        role__in=('owner', 'manager'),
    ).exists()


def _get_claim_for_store(claim_id, store):
    """Devuelve el reclamo si pertenece a un pedido con items de este store."""
    claim = get_object_or_404(
        OrderClaim.objects.select_related('order', 'opened_by'),
        id=claim_id,
    )
    # Verificar que el pedido tenga items de este store
    if not claim.order.items.filter(store=store).exists():
        raise Http404()
    return claim


@login_required(login_url='login')
def store_claim_detail(request, store_id, claim_id):
    """El comercio ve el detalle del reclamo + chat."""
    store = get_object_or_404(Store, id=store_id, is_active=True)
    if not _check_store_manager(request, store):
        raise Http404()

    claim = _get_claim_for_store(claim_id, store)
    mensajes = claim.messages.select_related('sender').all()
    form = OrderClaimMessageForm()

    # El comercio solo puede chatear mientras el cliente no haya confirmado
    puede_responder = claim.status in ('open', 'in_review')

    return render(request, 'stores/dashboard/claim_detail.html', {
        'store': store,
        'claim': claim,
        'claim_messages': mensajes,
        'form': form,
        'puede_responder': puede_responder,
    })


@login_required(login_url='login')
def store_claim_add_message(request, store_id, claim_id):
    """El comercio agrega un mensaje al reclamo."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Metodo no permitido')

    store = get_object_or_404(Store, id=store_id, is_active=True)
    if not _check_store_manager(request, store):
        raise Http404()

    claim = _get_claim_for_store(claim_id, store)

    if claim.status not in ('open', 'in_review'):
        messages.warning(request, 'Este reclamo ya no permite más mensajes.')
        return redirect('stores:store_claim_detail', store_id=store.id, claim_id=claim.pk)

    form = OrderClaimMessageForm(request.POST, request.FILES)
    if form.is_valid():
        msg = form.save(commit=False)
        msg.claim = claim
        msg.sender = request.user
        msg.is_system = False
        msg.save()

        # Si estaba abierto, pasa a "en revisión"
        if claim.status == 'open':
            claim.status = 'in_review'
            claim.save(update_fields=['status'])

        # Notificar al cliente
        notify(
            claim.opened_by,
            'system',
            f'Nueva respuesta - Reclamo #{claim.pk}',
            f'{store.name} respondió a tu reclamo.',
            link=f'/orders/claim/{claim.pk}/',
        )

        messages.success(request, 'Mensaje enviado al cliente.')
    else:
        messages.error(request, 'No se pudo enviar el mensaje.')

    return redirect('stores:store_claim_detail', store_id=store.id, claim_id=claim.pk)


@login_required(login_url='login')
def store_claim_resolve(request, store_id, claim_id):
    """El comercio marca el reclamo como resuelto."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Metodo no permitido')

    store = get_object_or_404(Store, id=store_id, is_active=True)
    if not _check_store_manager(request, store):
        raise Http404()

    claim = _get_claim_for_store(claim_id, store)

    if claim.status not in ('open', 'in_review'):
        messages.warning(request, 'Este reclamo ya fue resuelto o está cerrado.')
        return redirect('stores:store_claim_detail', store_id=store.id, claim_id=claim.pk)

    resolucion = (request.POST.get('resolution') or '').strip()
    if len(resolucion) < 20:
        messages.error(request, 'La resolución debe tener al menos 20 caracteres.')
        return redirect('stores:store_claim_detail', store_id=store.id, claim_id=claim.pk)

    # Adjunto opcional
    evidencia = request.FILES.get('resolution_evidence')

    claim.status = 'resolved'
    claim.resolution = resolucion
    claim.resolved_by = request.user
    claim.resolved_at = timezone.now()
    if evidencia:
        claim.resolution_evidence = evidencia
    claim.save(update_fields=[
        'status', 'resolution', 'resolved_by', 'resolved_at',
        'resolution_evidence',
    ])

    # Mensaje de sistema
    OrderClaimMessage.objects.create(
        claim=claim,
        sender=request.user,
        message=f'El comercio marcó el reclamo como resuelto.',
        is_system=True,
    )

    # Notificar al cliente
    notify(
        claim.opened_by,
        'system',
        f'Reclamo resuelto - {claim.order.reference_code}',
        f'{store.name} resolvió tu reclamo. Revísalo y confirma si estás conforme.',
        link=f'/orders/claim/{claim.pk}/',
    )

    messages.success(request, 'Reclamo marcado como resuelto. El cliente fue notificado.')
    return redirect('stores:store_claim_detail', store_id=store.id, claim_id=claim.pk)


@login_required(login_url='login')
def store_claim_escalate(request, store_id, claim_id):
    """El comercio escala el reclamo al superuser."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Metodo no permitido')

    store = get_object_or_404(Store, id=store_id, is_active=True)
    if not _check_store_manager(request, store):
        raise Http404()

    claim = _get_claim_for_store(claim_id, store)

    if claim.status in ESTADOS_CERRADOS:
        messages.warning(request, 'Este reclamo ya está cerrado.')
        return redirect('stores:store_claim_detail', store_id=store.id, claim_id=claim.pk)

    razon = (request.POST.get('escalate_reason') or '').strip()
    if len(razon) < 10:
        messages.error(request, 'Debes explicar el motivo (mínimo 10 caracteres).')
        return redirect('stores:store_claim_detail', store_id=store.id, claim_id=claim.pk)

    claim.status = 'escalated'
    claim.escalated_at = timezone.now()
    claim.escalated_reason = f'[Comercio] {razon}'
    claim.save(update_fields=['status', 'escalated_at', 'escalated_reason'])

    OrderClaimMessage.objects.create(
        claim=claim,
        sender=request.user,
        message=f'El comercio escaló el reclamo al administrador.',
        is_system=True,
    )

    # Notificar al superuser
    from django.contrib.auth.models import User
    for su in User.objects.filter(is_superuser=True, is_active=True):
        notify(
            su,
            'system',
            f'Reclamo escalado por comercio - {claim.order.reference_code}',
            f'{store.name} escaló un reclamo: {razon}',
            link=f'/admin/orders/orderclaim/{claim.pk}/change/',
        )

    messages.success(request, 'Reclamo escalado al administrador.')
    return redirect('stores:store_claim_detail', store_id=store.id, claim_id=claim.pk)


# ============================================================
# VISTA DE LISTA (seccion de reclamos del comercio)
# ============================================================


class StoreClaimsListView(RoleContextMixin, ManagerRequiredMixin, ListView):
    """Lista de reclamos que afectan pedidos de este comercio."""
    template_name = "stores/dashboard/claim_list.html"
    context_object_name = "claims"
    paginate_by = 20

    def get_queryset(self):
        from apps.orders.models import Order, OrderClaim

        store = self.get_store()
        status_filter = self.request.GET.get('status', 'active')

        # IDs de pedidos que tengan items de este comercio
        order_ids = Order.objects.filter(
            items__store=store
        ).values_list('id', flat=True).distinct()

        qs = OrderClaim.objects.filter(
            order_id__in=order_ids
        ).select_related('order', 'opened_by', 'resolved_by').order_by('-created_at')

        # Filtros por estado
        if status_filter == 'active':
            qs = qs.filter(status__in=('open', 'in_review', 'escalated'))
        elif status_filter == 'open':
            qs = qs.filter(status='open')
        elif status_filter == 'in_review':
            qs = qs.filter(status='in_review')
        elif status_filter == 'resolved':
            qs = qs.filter(status='resolved')
        elif status_filter == 'escalated':
            qs = qs.filter(status='escalated')
        elif status_filter == 'closed':
            qs = qs.filter(status__in=('closed', 'rejected'))
        # 'all' no filtra

        return qs

    def get_context_data(self, **kwargs):
        from apps.orders.models import Order, OrderClaim

        context = super().get_context_data(**kwargs)
        store = self.get_store()
        context['store'] = store
        context['current_status'] = self.request.GET.get('status', 'active')

        # Contadores por estado
        order_ids = Order.objects.filter(
            items__store=store
        ).values_list('id', flat=True).distinct()

        base = OrderClaim.objects.filter(order_id__in=order_ids)

        context['count_active'] = base.filter(
            status__in=('open', 'in_review', 'escalated')
        ).count()
        context['count_open'] = base.filter(status='open').count()
        context['count_in_review'] = base.filter(status='in_review').count()
        context['count_resolved'] = base.filter(status='resolved').count()
        context['count_escalated'] = base.filter(status='escalated').count()
        context['count_closed'] = base.filter(
            status__in=('closed', 'rejected')
        ).count()
        context['count_all'] = base.count()

        return context
