from django.contrib import admin
from .models import Store, StoreUserPermission


class StoreUserPermissionInline(admin.TabularInline):
    model = StoreUserPermission
    extra = 1
    fields = ("user", "role", "is_active")
    autocomplete_fields = ("user",)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "legal_name", "rif", "payment_region", "is_active")
    list_filter = ("payment_region", "is_active")
    search_fields = ("name", "legal_name", "rif")
    inlines = [StoreUserPermissionInline]

    fieldsets = (
        ("Datos del comercio", {
            "fields": (
                "name", "legal_name", "rif", "logo", "description",
                "address", "phone", "email",
            )
        }),
        ("Entrega", {
            "fields": (
                "offers_delivery", "delivery_fee", "has_24_7_schedule",
            )
        }),
        ("Region de pagos", {
            "fields": ("payment_region",),
            "description": (
                "Determina que metodos de pago se muestran al comercio "
                "y al cliente. Los campos de la region NO activa se ignoran."
            )
        }),
        ("Metodos de pago Venezuela (solo si region = VE)", {
            "classes": ("collapse",),
            "fields": (
                "accepts_transfer",
                "bank_name", "account_number", "account_holder", "document",
                "accepts_mobile_payment",
                "mobile_payment_bank", "mobile_document", "payment_phone",
                "payment_email", "payment_notes",
            )
        }),
        ("Metodos de pago Mexico (solo si region = MX)", {
            "classes": ("collapse",),
            "fields": (
                "mx_accepts_spei",
                "mx_spei_clabe", "mx_spei_holder", "mx_spei_bank",
                "mx_accepts_mercadopago",
                "mx_mercadopago_alias",
                "mx_accepts_paypal",
                "mx_paypal_email",
                "mx_payment_notes",
            )
        }),
        ("Estado", {
            "fields": ("is_active", "created_at"),
        }),
    )

    readonly_fields = ("created_at",)


@admin.register(StoreUserPermission)
class StoreUserPermissionAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "role", "is_active")
    list_filter = ("store", "role", "is_active")
    search_fields = ("user__username", "store__name")
