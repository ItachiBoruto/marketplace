from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.cart.models import Cart

from .forms import PaymentForm
from .models import Order, OrderItem


@login_required(login_url='login')
def checkout(request):
    """Muestra el resumen del pedido + datos bancarios + formulario de pago."""
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('cart:view')

    items = cart.items.select_related('product', 'product__store').all()

    if not items:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('cart:view')

    # Validar stock antes de continuar
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
            with transaction.atomic():
                # Crear el pedido
                order = form.save(commit=False)
                order.user = request.user
                order.total = cart.get_total()
                order.status = 'payment_submitted'
                order.save()

                # Crear los items del pedido
                for cart_item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        store=cart_item.product.store,
                        product_name=cart_item.product.name,
                        product_price=cart_item.price,
                        quantity=cart_item.quantity,
                    )

                # Vaciar el carrito
                cart.items.all().delete()

            messages.success(
                request,
                f'¡Pedido #{order.pk} registrado! Verificaremos tu pago pronto.'
            )
            return redirect('orders:success', order_id=order.pk)
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
    """Página de confirmación después de registrar el pago."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/success.html', {'order': order})


@login_required(login_url='login')
def order_list(request):
    """Lista de pedidos del usuario."""
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'orders/list.html', {'orders': orders})


@login_required(login_url='login')
def order_detail(request, order_id):
    """Detalle de un pedido específico del usuario."""
    order = get_object_or_404(
        Order.objects.prefetch_related('items__store'),
        id=order_id, user=request.user
    )
    return render(request, 'orders/detail.html', {'order': order})