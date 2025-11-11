from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0026_alter_quiz_options_alter_quizcategory_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='exam_allowed_incorrect',
            field=models.IntegerField(default=3, help_text='Экзамен завершается при достижении лимита неправильных ответов. 0 — без ограничения.', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(200)], verbose_name='Допустимые ошибки'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='exam_time_limit',
            field=models.IntegerField(default=30, help_text='Сколько минут даётся на прохождение экзамена', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(360)], verbose_name='Лимит времени (минуты)'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='exam_total_questions',
            field=models.IntegerField(default=10, help_text='Максимальное количество вопросов в экзаменационной попытке (ограничивает число разделов)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(200)], verbose_name='Количество вопросов в экзамене'),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='allowed_incorrect_answers',
            field=models.IntegerField(default=0, help_text='Сохраняем настройку на момент начала попытки', verbose_name='Лимит ошибок'),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='failure_reason',
            field=models.CharField(choices=[('', 'Успешно завершено'), ('timeout', 'Время вышло'), ('incorrect_limit', 'Превышен лимит ошибок')], default='', max_length=20, verbose_name='Причина завершения'),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='incorrect_answers',
            field=models.IntegerField(default=0, verbose_name='Неправильных ответов'),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='max_questions',
            field=models.IntegerField(default=0, help_text='Сохраняем настройку на момент начала попытки', verbose_name='Лимит вопросов'),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='time_limit_seconds',
            field=models.IntegerField(default=0, help_text='Сохраняем настройку на момент начала попытки', verbose_name='Лимит времени (сек)'),
        ),
        migrations.RemoveField(
            model_name='quiz',
            name='pass_score',
        ),
        migrations.AlterField(
            model_name='quiz',
            name='questions_per_category',
            field=models.IntegerField(default=5, help_text='Общая настройка для распределения вопросов по разделам', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(50)], verbose_name='Вопросов из каждого раздела'),
        ),
    ]
