"""Vistas para solicitudes de cambio de datos bancarios."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.notifications.models import notify, notify_superusers

from .forms import PaymentChangeRequestForm
from .models import Store, StorePaymentChangeRequest, StoreUserPermission


def _is_owner(request, store):
    """True si el usuario es owner (o superuser) del comercio."""
    if request.user.is_superuser:
        return True
    return StoreUserPermission.objects.filter(
        user=request.user, store=store,
        role='owner', is_active=True
    ).exists()


def _is_superuser(request):
    return request.user.is_authenticated and request.user.is_superuser


# ============================================================
# VISTAS PARA EL OWNER
# ============================================================
@login_required(login_url='login')
def request_payment_change(request, store_id):
    """Formulario para que el owner solicite cambio de datos bancarios."""
    store = get_object_or_404(Store, id=store_id)

    if not _is_owner(request, store):
        raise Http404("Solo el propietario puede solicitar cambios.")

    # Verificar si hay una solicitud pendiente
    existing = StorePaymentChangeRequest.objects.filter(
        store=store, status='pending'
    ).first()

    if existing:
        messages.info(
            request,
            f'Ya tienes una solicitud pendiente (#{existing.pk}). '
            f'Espera la aprobación del administrador.'
        )
        return redirect('stores:payment_change_status', store_id=store.id)

    if request.method == 'POST':
        form = PaymentChangeRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.store = store
            req.requested_by = request.user

            # Snapshot del estado actual
            req.old_bank_name = store.bank_name or ''
            req.old_account_number = store.account_number or ''
            req.old_account_holder = store.account_holder or ''
            req.old_document = store.document or ''
            req.old_mobile_payment_bank = store.mobile_payment_bank or ''
            req.old_mobile_document = store.mobile_document or ''
            req.old_payment_phone = store.payment_phone or ''

            req.save()

            # Notificar a todos los superusers
            notify_superusers(
                'system',
                f'💳 Solicitud de cambio bancario - {store.name}',
                f'{request.user.username} solicita cambiar los datos bancarios. '
                f'Revisa el panel para aprobar o rechazar.',
                link='/orders/panel/payment-requests/'
            )

            messages.success(
                request,
                'Solicitud enviada. El administrador la revisará y aprobará pronto.'
            )
            return redirect('stores:payment_change_status', store_id=store.id)
    else:
        # Pre-llenar con los valores actuales
        form = PaymentChangeRequestForm(initial={
            'new_bank_name': store.bank_name or '',
            'new_account_number': store.account_number or '',
            'new_account_holder': store.account_holder or '',
            'new_document': store.document or '',
            'new_mobile_payment_bank': store.mobile_payment_bank or '',
            'new_mobile_document': store.mobile_document or '',
            'new_payment_phone': store.payment_phone or '',
        })

    return render(request, 'stores/dashboard/payment_change_request.html', {
        'store': store,
        'form': form,
    })


@login_required(login_url='login')
def payment_change_status(request, store_id):
    """Muestra el estado de las solicitudes de cambio del comercio."""
    store = get_object_or_404(Store, id=store_id)

    if not _is_owner(request, store):
        raise Http404()

    requests = StorePaymentChangeRequest.objects.filter(
        store=store
    ).order_by('-created_at')[:10]

    pending = [r for r in requests if r.status == 'pending']

    return render(request, 'stores/dashboard/payment_change_status.html', {
        'store': store,
        'requests': requests,
        'pending': pending[0] if pending else None,
    })


# ============================================================
# VISTAS PARA EL SUPERUSER
# ============================================================
@login_required(login_url='login')
def pending_payment_requests(request):
    """Lista de solicitudes pendientes (solo superuser)."""
    if not _is_superuser(request):
        raise Http404()

    requests = StorePaymentChangeRequest.objects.filter(
        status='pending'
    ).select_related('store', 'requested_by').order_by('-created_at')

    history = StorePaymentChangeRequest.objects.exclude(
        status='pending'
    ).select_related('store', 'requested_by', 'reviewed_by').order_by('-reviewed_at')[:20]

    return render(request, 'superadmin/payment_requests.html', {
        'requests': requests,
        'history': history,
    })


@login_required(login_url='login')
def approve_payment_request(request, request_id):
    """Aprueba una solicitud de cambio (solo superuser)."""
    if not _is_superuser(request):
        raise Http404()
    if request.method != 'POST':
        return HttpResponseBadRequest('Metodo no permitido')

    req = get_object_or_404(StorePaymentChangeRequest, id=request_id, status='pending')
    store = req.store

    # Aplicar los cambios al Store
    store.bank_name = req.new_bank_name or ''
    store.account_number = req.new_account_number or ''
    store.account_holder = req.new_account_holder or ''
    store.document = req.new_document or ''
    store.mobile_payment_bank = req.new_mobile_payment_bank or ''
    store.mobile_document = req.new_mobile_document or ''
    store.payment_phone = req.new_payment_phone or ''
    store.save(update_fields=[
        'bank_name', 'account_number', 'account_holder', 'document',
        'mobile_payment_bank', 'mobile_document', 'payment_phone'
    ])

    # Marcar la solicitud como aprobada
    req.status = 'approved'
    req.reviewed_by = request.user
    req.reviewed_at = timezone.now()
    req.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

    # Notificar al owner
    notify(
        req.requested_by,
        'system',
        f'✅ Cambio bancario aprobado - {store.name}',
        'Los nuevos datos bancarios ya están activos.',
        link=f'/stores/dashboard/{store.id}/payment-change/status/'
    )

    messages.success(
        request,
        f'Solicitud #{req.pk} aprobada. Los datos bancarios de {store.name} fueron actualizados.'
    )
    return redirect('orders:payment_requests')


@login_required(login_url='login')
def reject_payment_request(request, request_id):
    """Rechaza una solicitud de cambio (solo superuser)."""
    if not _is_superuser(request):
        raise Http404()
    if request.method != 'POST':
        return HttpResponseBadRequest('Metodo no permitido')

    req = get_object_or_404(StorePaymentChangeRequest, id=request_id, status='pending')
    reason = request.POST.get('rejection_reason', '').strip()

    if not reason:
        messages.error(request, 'Debes indicar el motivo del rechazo.')
        return redirect('orders:payment_requests')

    req.status = 'rejected'
    req.reviewed_by = request.user
    req.reviewed_at = timezone.now()
    req.rejection_reason = reason
    req.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason'])

    # Notificar al owner
    notify(
        req.requested_by,
        'system',
        f'❌ Cambio bancario rechazado - {req.store.name}',
        f'Motivo: {reason}',
        link=f'/stores/dashboard/{req.store.id}/payment-change/status/'
    )

    messages.success(request, f'Solicitud #{req.pk} rechazada.')
    return redirect('orders:payment_requests')
