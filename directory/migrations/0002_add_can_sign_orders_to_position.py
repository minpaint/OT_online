from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='can_sign_orders',
            field=models.BooleanField(
                default=False,
                verbose_name="Может подписывать распоряжения",
                help_text="Указывает, может ли сотрудник с этой должностью подписывать распоряжения"
            ),
        ),
    ]