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
    """Checkout: resumen del pedido + datos bancarios + formulario de pago."""
    # Expira reservas vencidas antes de procesar
    expire_old_reservations()

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('cart:view')

    items = cart.items.select_related('product', 'product__store').all()

    if not items:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('cart:view')

    # Validación previa de stock (solo para mostrar aviso rápido)
    for item in items:
        if item.quantity > item.product.stock:
            messages.error(
                request,
                f'No hay suficiente stock de "{item.product.name}". '
                f'Disponibles: {item.product.stock}.'
            )
            return redirect('cart:view')

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment_data = {
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
                )
                messages.success(
                    request,
                    f'¡Pedido #{order.pk} registrado! Verificaremos tu pago pronto.'
                )
                return redirect('orders:success', order_id=order.pk)
            except InsufficientStockError as e:
                messages.error(request, str(e))
                return redirect('cart:view')
            except EmptyCartError:
                messages.warning(request, 'Tu carrito está vacío.')
                return redirect('cart:view')
    else:
        form = PaymentForm()

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'items': items,
        'form': form,
        'bank_info': settings.BANK_INFO,
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

