from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('price',)
    autocomplete_fields = ('product',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_total_items', 'get_total', 'updated_at')
    search_fields = ('user__username',)
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'price')
    list_filter = ('cart__user',)
    search_fields = ('product__name', 'cart__user__username')