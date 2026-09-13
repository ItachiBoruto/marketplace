from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_name', 'store', 'quantity', 'product_price', 'status')
    readonly_fields = ('product_name', 'product_price')
    autocomplete_fields = ('store',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'status', 'total', 'get_items_count',
        'payment_bank', 'payment_reference', 'created_at'
    )
    list_filter = ('status', 'payment_bank', 'created_at')
    search_fields = ('user__username', 'payment_reference')
    readonly_fields = ('created_at', 'updated_at', 'total')
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Información general', {
            'fields': ('user', 'status', 'total', 'notes')
        }),
        ('Pago', {
            'fields': (
                'payment_bank', 'payment_reference', 'payment_date',
                'payment_proof'
            )
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Items'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_name', 'store', 'quantity', 'product_price', 'status')
    list_filter = ('status', 'store')
    search_fields = ('product_name', 'order__user__username', 'order__payment_reference')