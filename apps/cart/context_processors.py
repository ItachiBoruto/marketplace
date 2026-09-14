from .models import Cart


def cart_count(request):
    """Inyecta el numero de items del carrito en todos los templates."""
    if not request.user.is_authenticated:
        return {"cart_count": 0}
    try:
        cart = Cart.objects.get(user=request.user)
        return {"cart_count": cart.get_total_items()}
    except Cart.DoesNotExist:
        return {"cart_count": 0}
