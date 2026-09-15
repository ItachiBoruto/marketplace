from django.db import migrations, models
import secrets
import string
from django.utils import timezone


def backfill_reference_codes(apps, schema_editor):
    """Rellena reference_code para pedidos existentes."""
    Order = apps.get_model('orders', 'Order')

    for order in Order.objects.filter(reference_code__isnull=True):
        # Usar la fecha de creación del pedido si existe
        created = order.created_at if hasattr(order, 'created_at') and order.created_at else timezone.now()
        for _ in range(10):
            suffix = ''.join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(4)
            )
            code = f"ORD-{created.strftime('%y%m')}-{suffix}"
            if not Order.objects.filter(reference_code=code).exists():
                order.reference_code = code
                order.save(update_fields=['reference_code'])
                break


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_order_delivery_address_order_shipping_fee_and_more'),
    ]

    operations = [
        # Paso 1: agregar campo sin unique (para permitir NULLs duplicados temporalmente)
        migrations.AddField(
            model_name='order',
            name='reference_code',
            field=models.CharField(
                blank=True, null=True, max_length=20,
                verbose_name='Código de pedido',
                help_text='Se genera automáticamente. Ej: ORD-2609-A7B3'
            ),
        ),
        # Paso 2: rellenar los pedidos existentes
        migrations.RunPython(backfill_reference_codes, migrations.RunPython.noop),
        # Paso 3: aplicar unique
        migrations.AlterField(
            model_name='order',
            name='reference_code',
            field=models.CharField(
                blank=True, null=True, max_length=20, unique=True,
                verbose_name='Código de pedido',
                help_text='Se genera automáticamente. Ej: ORD-2609-A7B3'
            ),
        ),
    ]
