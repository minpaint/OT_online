from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from .base import BaseModel
from .organizational_unit import OrganizationalUnit


class Position(BaseModel):
    """Должности"""
    name = models.CharField('Название должности', max_length=255)
    organizational_unit = models.ForeignKey(
        OrganizationalUnit,
        on_delete=models.CASCADE,
        verbose_name='Подразделение',
        limit_choices_to={
            'unit_type__in': ['department', 'division']
        }
    )

    # Остальные поля остаются без изменений
    is_electrical_personnel = models.BooleanField(
        'Электротехнический персонал',
        default=False
    )
    electrical_safety_group = models.IntegerField(
        'Группа по электробезопасности',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    is_internship_supervisor = models.BooleanField(
        'Может быть руководителем стажировки',
        default=False
    )
    internship_period = models.IntegerField(
        'Период стажировки (дней)',
        validators=[MinValueValidator(1)],
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        ordering = ['name']
        # Добавляем уникальность для названия должности в пределах подразделения
        unique_together = [('name', 'organizational_unit')]

    def __str__(self):
        return f"{self.name} ({self.organizational_unit.get_full_path()})"

    def clean(self):
        if self.organizational_unit:
            # Проверяем, что это подразделение или отдел
            if self.organizational_unit.unit_type not in ['department', 'division']:
                raise ValidationError('Должность может быть создана только в подразделении или отделе')

            # Если это подразделение, проверяем что у него нет отделов
            if self.organizational_unit.unit_type == 'department':
                if self.organizational_unit.get_children().exists():
                    raise ValidationError(
                        'Должность не может быть создана в подразделении, у которого есть отделы'
                    )