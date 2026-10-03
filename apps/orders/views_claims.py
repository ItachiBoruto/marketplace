# -*- coding: utf-8 -*-
"""
Vistas del sistema de reclamos.

Endpoints:
- claim_create: cliente abre un reclamo
- claim_detail: cliente ve el detalle + chat
- claim_add_message: cliente agrega un mensaje
- claim_close: cliente acepta la resolución y cierra
- claim_escalate: cliente no conforme, escala al superuser
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.notifications.models import notify
from apps.utils.async_tasks import run_async

from .forms import OrderClaimForm, OrderClaimMessageForm
from .models import Order, OrderClaim, OrderClaimMessage


# Estados del pedido en los que SE PUEDE abrir un reclamo
ESTADOS_RECLAMABLES = ('payment_submitted', 'confirmed', 'shipped', 'completed')

# Estados del reclamo considerados "activos"
ESTADOS_ACTIVOS = ('open', 'in_review', 'resolved', 'escalated')


def _can_claim(order):
    """El pedido puede tener un reclamo abierto."""
    if order.status not in ESTADOS_RECLAMABLES:
        return False
    # Si ya tiene uno activo, no puede crear otro
    if hasattr(order, 'claim') and order.claim.status in ESTADOS_ACTIVOS:
        return False
    return True


@login_required(login_url='login')
def claim_create(request, order_id):
    """Cliente abre un reclamo sobre uno de sus pedidos."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Validar que se puede reclamar
    if not _can_claim(order):
        if hasattr(order, 'claim'):
            messages.info(request, 'Ya tienes un reclamo activo para este pedido.')
            return redirect('orders:claim_detail', claim_id=order.claim.pk)
        messages.warning(request, 'Este pedido no puede ser reclamado.')
        return redirect('orders:detail', order_id=order.pk)

    if request.method == 'POST':
        form = OrderClaimForm(request.POST, request.FILES)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.order = order
            claim.opened_by = request.user
            claim.status = 'open'
            claim.save()

            # Mensaje de sistema: reclamo abierto
            OrderClaimMessage.objects.create(
                claim=claim,
                sender=request.user,
                message='El cliente abrió este reclamo.',
                is_system=True,
            )

            # Notificar a los usuarios del comercio
            stores = set(item.store for item in order.items.select_related('store'))
            from apps.stores.models import StoreUserPermission
            for store in stores:
                users = StoreUserPermission.objects.filter(
                    store=store, is_active=True
                ).select_related('user')
                for perm in users:
                    notify(
                        perm.user,
                        'system',
                        f'Reclamo abierto - {order.reference_code}',
                        f'{request.user.username} abrió un reclamo: {claim.get_claim_type_display()}.',
                        link=f'/stores/dashboard/{store.id}/orders/{order.id}/',
                    )

            messages.success(
                request,
                'Reclamo enviado. El comercio ha sido notificado y te responderá pronto.'
            )
            return redirect('orders:claim_detail', claim_id=claim.pk)
    else:
        form = OrderClaimForm()

    return render(request, 'orders/claim_create.html', {
        'order': order,
        'form': form,
    })


@login_required(login_url='login')
def claim_detail(request, claim_id):
    """Cliente ve el detalle del reclamo + conversación."""
    claim = get_object_or_404(
        OrderClaim.objects.select_related('order', 'opened_by'),
        id=claim_id,
        opened_by=request.user,
    )

    messages_list = claim.messages.select_related('sender').all()
    form = OrderClaimMessageForm()

    # ¿Puede enviar mensajes en el chat? Solo en open/in_review
    puede_responder = claim.status in ('open', 'in_review')

    # ¿Puede confirmar la resolución (cerrar) o escalar?
    puede_confirmar = claim.status == 'resolved'

    return render(request, 'orders/claim_detail.html', {
        'claim': claim,
        'claim_messages': messages_list,
        'form': form,
        'puede_responder': puede_responder,
        'puede_confirmar': puede_confirmar,
    })


@login_required(login_url='login')
def claim_add_message(request, claim_id):
    """Cliente agrega un mensaje al reclamo."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Metodo no permitido')

    claim = get_object_or_404(
        OrderClaim,
        id=claim_id,
        opened_by=request.user,
    )

    if claim.status not in ('open', 'in_review'):
        messages.warning(request, 'Este reclamo ya no permite más mensajes.')
        return redirect('orders:claim_detail', claim_id=claim.pk)

    form = OrderClaimMessageForm(request.POST, request.FILES)
    if form.is_valid():
        msg = form.save(commit=False)
        msg.claim = claim
        msg.sender = request.user
        msg.is_system = False
        msg.save()

        # Si el comercio había resuelto y el cliente responde, vuelve a in_review
        if claim.status == 'resolved':
            claim.status = 'in_review'
            claim.save(update_fields=['status'])

        # Notificar al comercio
        order = claim.order
        stores = set(item.store for item in order.items.select_related('store'))
        from apps.stores.models import StoreUserPermission
        for store in stores:
            users = StoreUserPermission.objects.filter(
                store=store, is_active=True
            ).select_related('user')
            for perm in users:
                notify(
                    perm.user,
                    'system',
                    f'Nuevo mensaje en reclamo - {order.reference_code}',
                    f'{request.user.username} respondió en el reclamo.',
                    link=f'/stores/dashboard/{store.id}/orders/{order.id}/',
                )

        messages.success(request, 'Mensaje enviado.')
    else:
        messages.error(request, 'No se pudo enviar el mensaje.')

    return redirect('orders:claim_detail', claim_id=claim.pk)


@login_required(login_url='login')
def claim_close(request, claim_id):
    """Cliente acepta la resolución y cierra el reclamo."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Metodo no permitido')

    claim = get_object_or_404(
        OrderClaim,
        id=claim_id,
        opened_by=request.user,
    )

    if claim.status != 'resolved':
        messages.warning(request, 'Solo puedes cerrar un reclamo cuando el comercio lo haya resuelto.')
        return redirect('orders:claim_detail', claim_id=claim.pk)

    claim.status = 'closed'
    claim.closed_by = request.user
    claim.closed_at = timezone.now()
    claim.save(update_fields=['status', 'closed_by', 'closed_at'])

    OrderClaimMessage.objects.create(
        claim=claim,
        sender=request.user,
        message='El cliente dio por cerrado el reclamo.',
        is_system=True,
    )

    # Notificar al comercio
    order = claim.order
    stores = set(item.store for item in order.items.select_related('store'))
    from apps.stores.models import StoreUserPermission
    for store in stores:
        users = StoreUserPermission.objects.filter(
            store=store, is_active=True
        ).select_related('user')
        for perm in users:
            notify(
                perm.user,
                'system',
                f'Reclamo cerrado - {order.reference_code}',
                f'{request.user.username} cerró el reclamo.',
                link=f'/stores/dashboard/{store.id}/orders/{order.id}/',
            )

    messages.success(request, 'Reclamo cerrado. Gracias por tu paciencia.')
    return redirect('orders:claim_detail', claim_id=claim.pk)


@login_required(login_url='login')
def claim_escalate(request, claim_id):
    """Cliente no conforme con la resolución, escala al superuser."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Metodo no permitido')

    claim = get_object_or_404(
        OrderClaim,
        id=claim_id,
        opened_by=request.user,
    )

    if claim.status not in ('open', 'in_review', 'resolved'):
        messages.warning(request, 'Este reclamo no se puede escalar.')
        return redirect('orders:claim_detail', claim_id=claim.pk)

    razon = (request.POST.get('escalate_reason') or '').strip()
    if len(razon) < 10:
        messages.error(request, 'Debes explicar por qué no estás conforme (mínimo 10 caracteres).')
        return redirect('orders:claim_detail', claim_id=claim.pk)

    claim.status = 'escalated'
    claim.escalated_at = timezone.now()
    claim.escalated_reason = razon
    claim.save(update_fields=['status', 'escalated_at', 'escalated_reason'])

    OrderClaimMessage.objects.create(
        claim=claim,
        sender=request.user,
        message=f'Escalado al administrador. Motivo: {razon}',
        is_system=True,
    )

    # Notificar a superusers
    from django.contrib.auth.models import User
    for su in User.objects.filter(is_superuser=True, is_active=True):
        notify(
            su,
            'system',
            f'Reclamo escalado - {claim.order.reference_code}',
            f'{request.user.username} escaló un reclamo: {razon}',
            link=f'/admin/orders/orderclaim/{claim.pk}/change/',
        )

    messages.success(
        request,
        'Reclamo escalado al administrador. Te contactaremos pronto.'
    )
    return redirect('orders:claim_detail', claim_id=claim.pk)
