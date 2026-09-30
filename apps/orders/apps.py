from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'

    def ready(self):
        # Cargar signals cuando la app este lista
        import apps.orders.signals  # noqa: F401
