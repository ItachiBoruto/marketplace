from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0001_initial"),
        ("stores", "0004_userprofile"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="AuditLog"),
            ],
            database_operations=[],
        ),
    ]
