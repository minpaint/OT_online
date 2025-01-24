from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from .base import BaseModel  # Добавляем BaseModel


class OrganizationalUnit(MPTTModel, BaseModel):  # Добавляем BaseModel
    """Базовая модель для организационной структуры"""

    UNIT_TYPES = [
        ('organization', 'Организация'),
        ('department', 'Подразделение'),
        ('division', 'Отдел')
    ]

    name = models.CharField('Название', max_length=255)
    code = models.CharField('Код', max_length=50, blank=True)
    unit_type = models.CharField(
        'Тип подразделения',
        max_length=20,
        choices=UNIT_TYPES
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительское подразделение'
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Организационная единица'
        verbose_name_plural = 'Организационные единицы'
        # Добавляем уникальность для имени в пределах родителя
        unique_together = [('parent', 'name')]

    def __str__(self):
        return f"{self.get_unit_type_display()}: {self.name}"

    def get_full_path(self):
        """Получение полного пути подразделения"""
        ancestors = self.get_ancestors(include_self=True)
        return ' / '.join([unit.name for unit in ancestors])

    def clean(self):
        from django.core.exceptions import ValidationError

        # Проверяем корректность иерархии
        if self.unit_type == 'organization' and self.parent:
            raise ValidationError('Организация не может иметь родительское подразделение')

        if self.unit_type == 'department' and self.parent:
            if self.parent.unit_type != 'organization':
                raise ValidationError('Подразделение может быть создано только в организации')

        if self.unit_type == 'division' and self.parent:
            if self.parent.unit_type != 'department':
                raise ValidationError('Отдел может быть создан только в подразделении')

    def get_employees(self):
        """Получить всех сотрудников этого подразделения и его потомков"""
        from .employee import Employee
        return Employee.objects.filter(
            position__organizational_unit__in=self.get_descendants(include_self=True)
        )

    def get_positions(self):
        """Получить все должности этого подразделения и его потомков"""
        from .position import Position
        return Position.objects.filter(
            organizational_unit__in=self.get_descendants(include_self=True)
        )