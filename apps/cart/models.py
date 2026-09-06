from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Product

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"

    def __str__(self):
        if self.user:
            return f"Carrito de {self.user.username}"
        return f"Carrito (sesión: {self.session_key})"

    def get_total(self):
        return sum(item.get_total() for item in self.items.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Item del carrito"
        verbose_name_plural = "Items del carrito"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total(self):
        return self.price * self.quantity