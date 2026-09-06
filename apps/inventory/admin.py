from django.contrib import admin
from .models import StockMovement

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('store', 'product', 'quantity_change', 'movement_type', 'created_at')
    list_filter = ('store', 'movement_type')
    search_fields = ('store__name', 'product__name')
    readonly_fields = ('created_at',)