from django.conf import settings
from django.contrib import admin, messages

from apps.notifications.models import notify
from .models import ExchangeRate, Order, OrderItem, OrderClaim, OrderClaimMessage
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
        'reference_code', 'user', 'status', 'total', 'exchange_rate', 'get_items_count',
        'payment_bank', 'payment_reference',
        'reservation_expires_at', 'stock_released', 'created_at'
    )
    list_filter = ('status', 'payment_bank', 'stock_released', 'created_at')
    search_fields = ('reference_code', 'user__username', 'payment_reference')
    readonly_fields = (
        'reference_code', 'created_at', 'updated_at', 'total', 'exchange_rate',
        'reservation_expires_at', 'stock_released'
    )
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    actions = ['action_confirm_payment', 'action_cancel_order', 'action_extend_reservation']

    fieldsets = (
        ('Informacion general', {
            'fields': ('reference_code', 'user', 'status', 'total', 'exchange_rate', 'notes')
        }),
        ('Pago', {
            'fields': ('payment_bank', 'payment_reference', 'payment_date', 'payment_proof')
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

    @admin.action(description='Confirmar pago (marca como confirmado)')
    def action_confirm_payment(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status == 'payment_submitted':
                order.status = 'confirmed'
                order.save(update_fields=['status'])
                notify(
                    order.user,
                    'payment_confirmed',
                    f'Pago confirmado - Pedido {order.reference_code}',
                    'Verificamos tu pago. Los comercios están preparando tu pedido.',
                    link=f'/orders/{order.pk}/'
                )
                count += 1
        self.message_user(request, f'{count} pedido(s) confirmado(s).', messages.SUCCESS)

    @admin.action(description='Cancelar pedido (devuelve stock)')
    def action_cancel_order(self, request, queryset):
        count = 0
        for order in queryset:
            if order.status in ('payment_submitted', 'confirmed'):
                release_order_stock(order, reason='Cancelado por admin')
                order.status = 'cancelled'
                order.save(update_fields=['status'])
                count += 1
        self.message_user(request, f'{count} pedido(s) cancelado(s).', messages.SUCCESS)

    @admin.action(description='Extender reserva +30 min')
    def action_extend_reservation(self, request, queryset):
        from datetime import timedelta
        from django.utils import timezone
        count = 0
        for order in queryset:
            if order.reservation_expires_at and not order.stock_released:
                order.reservation_expires_at = timezone.now() + timedelta(minutes=settings.ORDER_RESERVATION_MINUTES)
                order.save(update_fields=['reservation_expires_at'])
                count += 1
        self.message_user(request, f'{count} reserva(s) extendida(s) +30 min.', messages.SUCCESS)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_name', 'store', 'quantity', 'product_price', 'status')
    list_filter = ('status', 'store')
    search_fields = ('product_name', 'order__user__username', 'order__payment_reference')


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """Solo superusers pueden ver/editar esta seccion."""
    list_display = ('fecha', 'valor', 'fuente', 'is_active', 'notas', 'actualizado_en')
    list_filter = ('fuente', 'is_active', 'fecha')
    search_fields = ('notas',)
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'

    fieldsets = (
        ('Tasa', {
            'fields': ('fecha', 'valor', 'fuente', 'is_active', 'notas'),
            'description': 'Si marcas "Usar esta tasa", todas las demas se desactivan automaticamente.'
        }),
    )

    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ============================================================
# ADMIN - Sistema de reclamos
# ============================================================


class OrderClaimMessageInline(admin.TabularInline):
    model = OrderClaimMessage
    extra = 0
    fields = ('sender', 'message', 'attachment', 'is_system', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False


@admin.register(OrderClaim)
class OrderClaimAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'order_link', 'claim_type', 'status',
        'opened_by', 'created_at', 'resolved_at',
    )
    list_filter = ('status', 'claim_type', 'created_at')
    search_fields = (
        'order__reference_code', 'opened_by__username',
        'description', 'resolution',
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderClaimMessageInline]

    fieldsets = (
        ('Información básica', {
            'fields': ('order', 'opened_by', 'claim_type', 'status', 'created_at', 'updated_at')
        }),
        ('Descripción del problema', {
            'fields': ('description', 'evidence')
        }),
        ('Resolución', {
            'fields': ('resolution', 'resolution_evidence', 'resolved_by', 'resolved_at')
        }),
        ('Escalado', {
            'classes': ('collapse',),
            'fields': ('escalated_at', 'escalated_reason')
        }),
        ('Cierre', {
            'classes': ('collapse',),
            'fields': ('closed_by', 'closed_at')
        }),
    )

    def order_link(self, obj):
        return obj.order.reference_code
    order_link.short_description = 'Pedido'
    order_link.admin_order_field = 'order__reference_code'


@admin.register(OrderClaimMessage)
class OrderClaimMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'claim', 'sender', 'is_system', 'created_at')
    list_filter = ('is_system', 'created_at')
    search_fields = ('claim__order__reference_code', 'sender__username', 'message')
    readonly_fields = ('created_at',)
