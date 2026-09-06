from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'price', 'stock', 'is_available')
    list_filter = ('store', 'is_available')
    search_fields = ('name', 'keywords', 'store__name')
    fieldsets = (
        (None, {
            'fields': ('store', 'name', 'price', 'description', 'additional_info', 'image', 'stock', 'keywords', 'is_available')
        }),
    )