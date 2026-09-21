from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.cart.models import Cart

from .forms import PaymentForm
from .exchange import get_bcv_rate, invalidate_cache
from .models import Order
from .services import (
    EmptyCartError,
    InsufficientStockError,
    create_order_from_cart,
    expire_old_reservations,
)


@login_required(login_url='login')
def checkout(request):
    """Checkout: muestra items de UN comercio (por ?store=<id>) y permite pagar."""
    expire_old_reservations()

    # Determinar store_id desde GET o POST
    store_id = request.GET.get('store') or request.POST.get('store_id')
    store = None

    if store_id:
        from apps.stores.models import Store
        try:
            store = Store.objects.get(id=store_id, is_active=True)
        except Store.DoesNotExist:
            messages.error(request, 'El comercio seleccionado no existe.')
            return redirect('cart:view')

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('cart:view')

    # Filtrar items por comercio (o todos si no se especifica)
    items_qs = cart.items.select_related('product', 'product__store').all()
    if store is not None:
        items_qs = items_qs.filter(product__store=store)

    items = list(items_qs)

    if not items:
        messages.warning(request, 'No hay productos de este comercio en tu carrito.')
        return redirect('cart:view')

    # Si no se especificó store y hay varios comercios, redirigir al carrito
    if store is None:
        stores_in_cart = set(item.product.store_id for item in items)
        if len(stores_in_cart) > 1:
            messages.info(
                request,
                'Selecciona un comercio para pagar. Cada comercio se paga por separado.'
            )
            return redirect('cart:view')
        # Un solo comercio → tomar ese
        store = items[0].product.store

    # Validar stock
    for item in items:
        if item.quantity > item.product.stock:
            messages.error(
                request,
                f'No hay suficiente stock de "{item.product.name}". '
                f'Disponibles: {item.product.stock}.'
            )
            return redirect('cart:view')

    # ===== Verificar horario del comercio =====
    from apps.stores.schedule_utils import get_store_status
    store_status = get_store_status(store)

    # Verificar si esta abierto para retiro y delivery
    pickup_available = store_status['pickup']['is_open']
    delivery_available = store.offers_delivery and store_status['delivery']['is_open']

    # Si NO esta abierto para NINGUN metodo -> bloquear
    if not pickup_available and not delivery_available:
        # Determinar el mejor mensaje
        if not store.offers_delivery:
            reason = store_status['pickup']['reason'] or 'El comercio está cerrado.'
            next_open = store_status['pickup']['next_open']
        else:
            # Ambos estan cerrados
            reason = store_status['pickup']['reason'] or 'El comercio está cerrado.'
            next_open = store_status['pickup']['next_open'] or store_status['delivery']['next_open']

        messages.warning(
            request,
            f'🕐 {reason}'
            + (f' Vuelve a intentarlo cuando abra ({next_open}).' if next_open else '')
        )
        return redirect('cart:view')

    # Ajustar delivery_available segun horario
    if store.offers_delivery and not delivery_available:
        # Delivery cerrado, pero pickup abierto
        delivery_available = False  # Solo permitir retiro

    total_delivery_fee = store.delivery_fee if delivery_available else 0

    # Subtotal solo de estos items
    subtotal = sum(item.get_total() for item in items)

    if request.method == 'POST':
        form = PaymentForm(
            request.POST, request.FILES,
            delivery_available=delivery_available,
            pickup_available=pickup_available,
        )
        if form.is_valid():
            method = form.cleaned_data['shipping_method']
            shipping_fee = total_delivery_fee if method == 'delivery' else 0

            # ===== RE-VALIDAR HORARIO (por si cerro entre GET y POST) =====
            from apps.stores.schedule_utils import get_store_status
            current_status = get_store_status(store)

            if method == 'delivery' and not current_status['delivery']['is_open']:
                messages.error(
                    request,
                    '⚠️ El comercio dejó de aceptar pedidos por delivery. '
                    'Intenta con retiro en tienda o vuelve cuando abra.'
                )
                return redirect('cart:view')

            if method == 'pickup' and not current_status['pickup']['is_open']:
                messages.error(
                    request,
                    '⚠️ El comercio dejó de aceptar retiro en tienda. '
                    'Intenta con delivery o vuelve cuando abra.'
                )
                return redirect('cart:view')

            payment_data = {
                'shipping_method': method,
                'delivery_address': form.cleaned_data.get('delivery_address', ''),
                'shipping_fee': shipping_fee,
                'payment_bank': form.cleaned_data['payment_bank'],
                'payment_reference': form.cleaned_data['payment_reference'],
                'payment_date': form.cleaned_data['payment_date'],
                'payment_proof': form.cleaned_data.get('payment_proof'),
                'notes': form.cleaned_data.get('notes', ''),
            }
            try:
                order = create_order_from_cart(
                    user=request.user,
                    payment_data=payment_data,
                    cart=cart,
                    store=store,
                )
                messages.success(
                    request,
                    f'¡Pedido {order.reference_code} registrado! Verificaremos tu pago pronto.'
                )
                return redirect('orders:success', order_id=order.pk)
            except InsufficientStockError as e:
                messages.error(request, str(e))
                return redirect('cart:view')
            except EmptyCartError:
                messages.warning(request, 'No hay productos para procesar.')
                return redirect('cart:view')
    else:
        form = PaymentForm(
            delivery_available=delivery_available,
            pickup_available=pickup_available,
        )

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'items': items,
        'form': form,
        'store': store,
        'subtotal': subtotal,
        'bank_info': settings.BANK_INFO,
        'delivery_available': delivery_available,
        'pickup_available': pickup_available,
        'total_delivery_fee': total_delivery_fee,
        'store_status': store_status,
    })


@login_required(login_url='login')
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/success.html', {'order': order})


@login_required(login_url='login')
def order_list(request):
    expire_old_reservations()
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'orders/list.html', {'orders': orders})


@login_required(login_url='login')
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__store'),
        id=order_id, user=request.user
    )
    return render(request, 'orders/detail.html', {'order': order})


def payment_qr(request):
    """Genera un QR con los datos bancarios en texto plano (seguro)."""
    import qrcode
    from io import BytesIO
    from django.http import HttpResponse

    bank = settings.BANK_INFO

    data = (
        f"Datos de pago\n"
        f"Banco: {bank.get('bank_name', '')}\n"
        f"Titular: {bank.get('account_holder', '')}\n"
        f"Cedula: {bank.get('document', '')}\n"
        f"Cuenta: {bank.get('account_number', '')}\n"
        f"Telefono: {bank.get('phone', '')}"
    )

    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")


def cron_expire_reservations(request):
    """
    Endpoint para cron externo (cron-job.org, GitHub Actions, etc.).
    Protegido por token en query string.
    """
    token = request.GET.get('token', '')
    expected = getattr(settings, 'CRON_SECRET_TOKEN', '')
    if not expected or token != expected:
        return JsonResponse({'error': 'unauthorized'}, status=401)

    count = expire_old_reservations()
    return JsonResponse({'expired': count, 'ok': True})


def cron_update_bcv(request):
    token = request.GET.get('token', '')
    expected = getattr(settings, 'CRON_SECRET_TOKEN', '')
    if not expected or token != expected:
        return JsonResponse({'error': 'unauthorized'}, status=401)
    invalidate_cache()
    rate = get_bcv_rate()
    return JsonResponse({'rate': rate, 'ok': rate is not None})

