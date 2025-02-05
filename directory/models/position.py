# directory/models/position.py
from django.db import models
from django.core.exceptions import ValidationError
from smart_selects.db_fields import ChainedForeignKey
from directory.models.organization import Organization
from directory.models.subdivision import StructuralSubdivision
from directory.models.department import Department
from directory.models.document import Document
from directory.models.equipment import Equipment

class Position(models.Model):
    ELECTRICAL_GROUP_CHOICES = [
        ("I", "I"),
        ("II", "II"),
        ("III", "III"),
        ("IV", "IV"),
        ("V", "V"),
    ]

    position_name = models.CharField(max_length=255, verbose_name="Название")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="positions",
        verbose_name="Организация"
    )
    subdivision = ChainedForeignKey(
        StructuralSubdivision,
        chained_field="organization",
        chained_model_field="organization",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.PROTECT,
        verbose_name="Структурное подразделение",
        null=True,
        blank=True
    )
    department = ChainedForeignKey(
        Department,
        chained_field="subdivision",
        chained_model_field="subdivision",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Отдел"
    )
    safety_instructions_numbers = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Номера инструкций по ОТ"
    )
    electrical_safety_group = models.CharField(
        max_length=4,
        choices=ELECTRICAL_GROUP_CHOICES,
        blank=True,
        verbose_name="Группа по электробезопасности"
    )
    internship_period_days = models.PositiveIntegerField(
        default=0,
        verbose_name="Срок стажировки (дни)"
    )
    is_responsible_for_safety = models.BooleanField(
        default=False,
        verbose_name="Ответственный за ОТ"
    )
    is_electrical_personnel = models.BooleanField(
        default=False,
        verbose_name="Электротехнический персонал"
    )
    documents = models.ManyToManyField(
        Document,
        blank=True,
        related_name="positions",
        verbose_name="Документы"
    )
    equipment = models.ManyToManyField(
        Equipment,
        blank=True,
        related_name="positions",
        verbose_name="Оборудование"
    )

    def clean(self):
        if self.department and not self.subdivision:
            raise ValidationError({
                'department': 'Нельзя указать отдел без структурного подразделения'
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        parts = [self.position_name]
        if self.department:
            parts.append(f"({self.department})")
        elif self.subdivision:
            parts.append(f"({self.subdivision})")
        else:
            parts.append(f"({self.organization})")
        return " ".join(parts)

    class Meta:
        verbose_name = "Профессия/должность"
        verbose_name_plural = "Профессии/должности"
        ordering = ['position_name']