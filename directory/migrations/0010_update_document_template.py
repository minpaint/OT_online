# directory/migrations/xxxx_update_document_template.py
from django.db import migrations, models
import django.db.models.deletion


def mark_existing_templates_as_default(apps, schema_editor):
    """Помечает все существующие шаблоны как эталонные"""
    DocumentTemplate = apps.get_model('directory', 'DocumentTemplate')
    for template in DocumentTemplate.objects.all():
        template.is_default = True
        template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0010_update_document_template'),  # Предыдущая миграция
    ]

    operations = [
        migrations.AddField(
            model_name='documenttemplate',
            name='organization',
            field=models.ForeignKey(
                blank=True,
                help_text='Организация, для которой предназначен шаблон. Если не указана, шаблон считается эталонным.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='document_templates',
                to='directory.organization',
                verbose_name='Организация'
            ),
        ),
        migrations.AddField(
            model_name='documenttemplate',
            name='is_default',
            field=models.BooleanField(
                default=False,
                help_text='Указывает, является ли шаблон эталонным для всех организаций',
                verbose_name='Эталонный шаблон'
            ),
        ),
        migrations.RunPython(
            mark_existing_templates_as_default,
            reverse_code=migrations.RunPython.noop
        ),
        migrations.AddConstraint(
            model_name='documenttemplate',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_default=True),
                fields=('document_type',),
                name='unique_default_template_per_type'
            ),
        ),
    ]