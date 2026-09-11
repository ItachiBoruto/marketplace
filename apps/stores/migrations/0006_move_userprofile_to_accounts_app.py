from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("stores", "0005_move_auditlog_to_audit_app"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="UserProfile"),
            ],
            database_operations=[],
        ),
    ]
