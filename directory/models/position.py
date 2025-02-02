from django.db import models
from .organization import Organization
from .subdivision import StructuralSubdivision
from .department import Department
from .document import Document
from .equipment import Equipment
from smart_selects.db_fields import ChainedForeignKey

class Position(models.Model):
    """Профессии и должности."""
    ELECTRICAL_GROUP_CHOICES = [
        ("I", "I"),
        ("II", "II"),
        ("III", "III"),
        ("IV", "IV"),
        ("V", "V"),
    ]
    # Основные связи
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
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
        verbose_name="Структурное подразделение"
    )
    department = ChainedForeignKey(
        Department,
        chained_field="subdivision",
        chained_model_field="subdivision",
        show_all=False,
        auto_choose=True,
        sort=True,
        null=True,
        blank=True,
        verbose_name="Отдел"
    )
    # Остальные поля
    position_name = models.CharField(max_length=255, verbose_name="Название")
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

    def __str__(self):
        return self.position_name

    class Meta:
        verbose_name = "Профессия/должность"
        verbose_name_plural = "Профессии/должности"
