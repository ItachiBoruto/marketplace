from django.contrib import admin
from .models import Store, StoreUserPermission


class StoreUserPermissionInline(admin.TabularInline):
    model = StoreUserPermission
    extra = 1
    fields = ("user", "role", "is_active")
    autocomplete_fields = ("user",)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "legal_name", "rif", "is_active")
    search_fields = ("name", "legal_name", "rif")
    inlines = [StoreUserPermissionInline]


@admin.register(StoreUserPermission)
class StoreUserPermissionAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "role", "is_active")
    list_filter = ("store", "role", "is_active")
    search_fields = ("user__username", "store__name")
