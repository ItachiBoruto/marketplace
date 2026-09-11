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
                    name="UserProfile",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("phone", models.CharField(blank=True, max_length=20, null=True, verbose_name="Teléfono")),
                        ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        "verbose_name": "Perfil de usuario",
                        "verbose_name_plural": "Perfiles de usuario",
                        "db_table": "stores_userprofile",
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
