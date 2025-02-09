from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='commission_role',
            field=models.CharField(
                choices=[
                    ('chairman', '👑 Председатель комиссии'),
                    ('member', '👤 Член комиссии'),
                    ('secretary', '📝 Секретарь комиссии'),
                    ('none', '❌ Не участвует в комиссии')
                ],
                default='none',
                help_text='Укажите роль сотрудника в комиссии',
                max_length=10,
                verbose_name='Роль в комиссии'
            ),
        ),
    ]