from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0027_update_quiz_exam_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='is_category_training',
            field=models.BooleanField(
                default=False,
                verbose_name='Авто-тренировка по разделу',
                help_text='Пометка для автоматически созданных тренировок по категориям.'
            ),
        ),
    ]
