# Generated manually for SIZNorm model refactoring

from django.db import migrations, models


def migrate_groups_to_conditions(apps, schema_editor):
    """
    🔄 Перенос данных из SIZNormGroup в поле condition модели SIZNorm
    """
    SIZNorm = apps.get_model('directory', 'SIZNorm')
    SIZNormGroup = apps.get_model('directory', 'SIZNormGroup')

    print("Начинаем перенос данных из групп в условия...")

    # Для каждой нормы, у которой есть группа, копируем имя группы в поле condition
    migrated_count = 0
    error_count = 0

    # Сначала убедимся, что мы можем получить все группы
    groups = list(SIZNormGroup.objects.all())
    print(f"Найдено {len(groups)} групп СИЗ")

    for norm in SIZNorm.objects.filter(group__isnull=False):
        try:
            group_name = norm.group.name
            norm.condition = group_name
            norm.save(update_fields=['condition'])
            migrated_count += 1
            if migrated_count % 50 == 0:
                print(f"Перенесено {migrated_count} записей...")
        except Exception as e:
            error_count += 1
            print(f"Ошибка при обработке нормы {norm.id}: {e}")

    print(f"Миграция завершена. Успешно перенесено {migrated_count} записей. Ошибок: {error_count}")


def reverse_migration(apps, schema_editor):
    """
    ↩️ Обратная миграция (для отката)
    """
    print("Обратная миграция не поддерживается. Данные не будут восстановлены.")


class Migration(migrations.Migration):
    # Исправлена зависимость на существующую миграцию
    dependencies = [
        ('directory', '0012_siz_remove_positionppe_position_and_more'),
    ]

    operations = [
        # 1. Сначала добавляем поле condition, если его еще нет
        migrations.AddField(
            model_name='siznorm',
            name='condition',
            field=models.CharField(
                blank=True,
                default='',
                help_text="Например: 'При влажной уборке помещений', 'При работе на высоте' и т.д.",
                max_length=255,
                verbose_name='Условие выдачи'
            ),
            preserve_default=False,
        ),

        # 2. Переносим данные из групп в условия
        migrations.RunPython(
            migrate_groups_to_conditions,
            reverse_code=reverse_migration
        ),

        # 3. Меняем опции модели (порядок сортировки)
        migrations.AlterModelOptions(
            name='siznorm',
            options={
                'ordering': ['position', 'condition', 'order', 'siz__name'],
                'verbose_name': 'Норма выдачи СИЗ',
                'verbose_name_plural': 'Нормы выдачи СИЗ'
            },
        ),

        # 4. Меняем уникальное ограничение
        migrations.AlterUniqueTogether(
            name='siznorm',
            unique_together={('position', 'siz', 'condition')},
        ),

        # 5. Удаляем поле group
        migrations.RemoveField(
            model_name='siznorm',
            name='group',
        ),

        # 6. Удаляем модель SIZNormGroup
        migrations.DeleteModel(
            name='SIZNormGroup',
        ),
    ]