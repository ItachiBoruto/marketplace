from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.products.models import Product
from .models import Cart, CartItem


def get_or_create_cart(request):
    """
    Devuelve el carrito del usuario autenticado.
    Solo se llama desde vistas con @login_required.
    """
    cart, created = Cart.objects.get_or_create(user=request.user)
    return cart



@login_required(login_url='login')
def add_to_cart(request, product_id):
    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('Accept', '')
    )

    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = get_or_create_cart(request)

    # --- Sin stock ---
    if product.stock <= 0:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': f'"{product.name}" no tiene stock.',
                'cart_count': cart.get_total_items(),
            }, status=400)
        messages.error(request, f'"{product.name}" no está disponible en stock.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'price': product.price, 'quantity': 1}
    )

    # --- Ya estaba en el carrito ---
    if not created:
        if cart_item.quantity + 1 > product.stock:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': f'No hay suficiente stock. Disponibles: {product.stock}.',
                    'cart_count': cart.get_total_items(),
                }, status=400)
            messages.warning(request, f'No hay suficiente stock de "{product.name}". Disponibles: {product.stock}.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        cart_item.quantity += 1
        cart_item.save()

    cart_count = cart.get_total_items()

    if is_ajax:
        return JsonResponse({
            'success': True,
            'product_name': product.name,
            'cart_count': cart_count,
            'message': f'"{product.name}" agregado',
        })

    messages.success(request, f'"{product.name}" agregado al carrito.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required(login_url='login')
def view_cart(request):
    """Carrito segmentado por comercio."""
    cart = get_or_create_cart(request)

    # Agrupar items por comercio. Orden descendente por id:
    # los items agregados mas recientemente aparecen primero.
    items = cart.items.select_related('product', 'product__store').order_by('-id')

    groups_dict = {}
    for item in items:
        store = item.product.store
        if store.id not in groups_dict:
            groups_dict[store.id] = {
                'store': store,
                'items': [],
                'subtotal': 0,
                'delivery_fee': store.delivery_fee if store.offers_delivery else 0,
                'offers_delivery': store.offers_delivery,
                # id del item mas reciente que se agrego en este grupo
                'first_item_id': item.id,
            }
        groups_dict[store.id]['items'].append(item)
        groups_dict[store.id]['subtotal'] += item.get_total()

    # Convertir a lista y calcular totales
    groups = []
    for g in groups_dict.values():
        g['has_delivery'] = g['offers_delivery'] and g['delivery_fee'] > 0
        g['total'] = g['subtotal'] + (g['delivery_fee'] if g['has_delivery'] else 0)
        groups.append(g)

    # Ordenar grupos por orden de llegada (el primer item que se agrego
    # de cada comercio define el orden)
    # Orden descendente: el comercio con el item mas reciente va primero
    groups.sort(key=lambda x: x['first_item_id'], reverse=True)

    grand_total = sum(g['total'] for g in groups)
    grand_total_no_delivery = sum(g['subtotal'] for g in groups)

    return render(request, 'cart/view.html', {
        'cart': cart,
        'groups': groups,
        'grand_total': grand_total,
        'grand_total_no_delivery': grand_total_no_delivery,
    })


@login_required(login_url='login')
def update_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            cart_item.delete()
            messages.info(request, 'Producto eliminado del carrito.')
        else:
            if quantity > cart_item.product.stock:
                messages.warning(request, f'No hay suficiente stock. Disponibles: {cart_item.product.stock}.')
                return redirect('cart:view')
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cantidad actualizada.')

    return redirect('cart:view')


@login_required(login_url='login')
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    messages.info(request, 'Producto eliminado del carrito.')
    return redirect('cart:view')