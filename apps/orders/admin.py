from django.contrib import admin, messages

from .models import Order, OrderItem
from .services import release_order_stock


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
        'payment_bank', 'payment_reference',
        'reservation_expires_at', 'stock_released', 'created_at'
    )
    list_filter = (
        'status', 'payment_bank', 'stock_released', 'created_at'
    )
    search_fields = ('user__username', 'payment_reference')
    readonly_fields = (
        'created_at', 'updated_at', 'total',
        'reservation_expires_at', 'stock_released'
    )
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    actions = ['action_confirm_payment', 'action_cancel_order', 'action_extend_reservation']

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
        ('Reserva de stock', {
            'fields': ('reservation_expires_at', 'stock_released')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Items'

    @admin.action(description='✅ Confirmar pago (marca como confirmado)')
    def action_confirm_payment(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status == 'payment_submitted':
                order.status = 'confirmed'
                order.save(update_fields=['status'])
                count += 1
        self.message_user(request, f'{count} pedido(s) confirmado(s).', messages.SUCCESS)

    @admin.action(description='❌ Cancelar pedido (devuelve stock)')
    def action_cancel_order(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status in ('payment_submitted', 'confirmed'):
                release_order_stock(order, reason='Cancelado por admin')
                order.status = 'cancelled'
                order.save(update_fields=['status'])
                count += 1
        self.message_user(request, f'{count} pedido(s) cancelado(s).', messages.SUCCESS)

    @admin.action(description='⏱️ Extender reserva +30 min')
    def action_extend_reservation(self, request, queryset):
        from datetime import timedelta
        from django.utils import timezone
        count = 0
        for order in queryset:
            if order.reservation_expires_at and not order.stock_released:
                order.reservation_expires_at = timezone.now() + timedelta(minutes=30)
                order.save(update_fields=['reservation_expires_at'])
                count += 1
        self.message_user(request, f'{count} reserva(s) extendida(s) +30 min.', messages.SUCCESS)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_name', 'store', 'quantity', 'product_price', 'status')
    list_filter = ('status', 'store')
    search_fields = ('product_name', 'order__user__username', 'order__payment_reference')
