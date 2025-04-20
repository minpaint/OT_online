# directory/migrations/0015_rename_maintenance_period_field.py
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0014_alter_equipment_maintenance_history'),
    ]

    operations = [
        migrations.RenameField(
            model_name='equipment',
            old_name='maintenance_period_days',
            new_name='maintenance_period_months',
        ),
    ]
