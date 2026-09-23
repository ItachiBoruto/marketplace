from django.contrib import admin
from .models import Category, Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'category', 'price', 'stock', 'is_available')
    list_filter = ('store', 'category', 'is_available')
    search_fields = ('name', 'keywords', 'store__name')
    fieldsets = (
        (None, {
            'fields': ('store', 'category', 'name', 'price', 'description', 'additional_info', 'image', 'stock', 'keywords', 'is_available')
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('emoji', 'name', 'slug', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')
    ordering = ('order',)
