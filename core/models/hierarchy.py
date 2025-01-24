from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

class OrganizationalUnit(MPTTModel):
    name = models.CharField('Наименование', max_length=255)
    code = models.CharField('Код', max_length=50, blank=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительская единица'
    )
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        verbose_name='Организация'
    )
    unit_type = models.CharField(
        'Тип подразделения',
        max_length=20,
        choices=[
            ('organization', 'Организация'),
            ('department', 'Подразделение'),
            ('division', 'Отдел')
        ]
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Организационная единица'
        verbose_name_plural = 'Организационные единицы'
        unique_together = [('parent', 'name')]

    def __str__(self):
        return f"{self.get_unit_type_display()}: {self.name}"

    def save(self, *args, **kwargs):
        if not self.parent and self.unit_type != 'organization':
            raise ValueError("Только организация может быть корневым элементом")
        super().save(*args, **kwargs)