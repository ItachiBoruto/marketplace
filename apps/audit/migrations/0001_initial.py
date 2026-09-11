from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("stores", "0004_userprofile"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="AuditLog",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("action", models.CharField(choices=[("create", "Creación"), ("update", "Actualización"), ("delete", "Eliminación"), ("stock_adjust", "Ajuste de stock"), ("permission_change", "Cambio de permisos"), ("login", "Inicio de sesión"), ("logout", "Cierre de sesión")], max_length=20)),
                        ("details", models.TextField()),
                        ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                        ("timestamp", models.DateTimeField(auto_now_add=True)),
                        ("store", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="stores.store")),
                        ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        "verbose_name": "Registro de auditoría",
                        "verbose_name_plural": "Registros de auditoría",
                        "ordering": ["-timestamp"],
                        "db_table": "stores_auditlog",
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
