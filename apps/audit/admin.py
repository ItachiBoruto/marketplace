from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "action", "ip_address", "timestamp")
    list_filter = ("action", "store")
    search_fields = ("user__username", "store__name", "details")
    readonly_fields = ("user", "store", "action", "details", "ip_address", "timestamp")
