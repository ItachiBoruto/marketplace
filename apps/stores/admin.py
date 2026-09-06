from django.contrib import admin
from .models import Store, StoreUserPermission, AuditLog

class StoreUserPermissionInline(admin.TabularInline):
    model = StoreUserPermission
    extra = 1
    fields = ('user', 'role', 'is_active')
    autocomplete_fields = ('user',)

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'legal_name', 'rif', 'is_active')
    search_fields = ('name', 'legal_name', 'rif')
    inlines = [StoreUserPermissionInline]

@admin.register(StoreUserPermission)
class StoreUserPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'store', 'role', 'is_active')
    list_filter = ('store', 'role', 'is_active')
    search_fields = ('user__username', 'store__name')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'store', 'action', 'ip_address', 'timestamp')
    list_filter = ('action', 'store')
    search_fields = ('user__username', 'store__name', 'details')
    readonly_fields = ('user', 'store', 'action', 'details', 'ip_address', 'timestamp')