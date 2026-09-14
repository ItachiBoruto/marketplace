from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.products.models import Product
from .models import Cart, CartItem


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        session_key = request.session.session_key
        if session_key:
            try:
                session_cart = Cart.objects.get(session_key=session_key)
                for item in session_cart.items.all():
                    item.cart = cart
                    item.save()
                session_cart.delete()
                request.session.delete()
            except Cart.DoesNotExist:
                pass
        return cart
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart


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


def view_cart(request):
    cart = get_or_create_cart(request)
    return render(request, 'cart/view.html', {'cart': cart})


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


def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    messages.info(request, 'Producto eliminado del carrito.')
    return redirect('cart:view')