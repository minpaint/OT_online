from django.db import models
from .organization import Organization
from .subdivision import StructuralSubdivision
from .department import Department
from .document import Document
from .equipment import Equipment

class Position(models.Model):
    """Справочник: Профессии и должности."""
    ELECTRICAL_GROUP_CHOICES = [
        ("I", "I"),
        ("II", "II"),
        ("III", "III"),
        ("IV", "IV"),
        ("V", "V"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="positions", verbose_name="Организация")
    subdivision = models.ForeignKey(StructuralSubdivision, on_delete=models.SET_NULL, null=True, blank=True, related_name="positions", verbose_name="Структурное подразделение")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="positions", verbose_name="Отдел")
    position_name = models.CharField(max_length=255, verbose_name="Название")
    safety_instructions_numbers = models.CharField(max_length=255, blank=True, verbose_name="Номера инструкций по ОТ")
    electrical_safety_group = models.CharField(max_length=4, choices=ELECTRICAL_GROUP_CHOICES, blank=True, verbose_name="Группа по электробезопасности")
    internship_period_days = models.PositiveIntegerField(default=0, verbose_name="Срок стажировки (дни)")
    is_responsible_for_safety = models.BooleanField(default=False, verbose_name="Ответственный за ОТ")
    is_electrical_personnel = models.BooleanField(default=False, verbose_name="Электротехнический персонал")
    documents = models.ManyToManyField(Document, blank=True, related_name="positions", verbose_name="Документы")
    equipment = models.ManyToManyField(Equipment, blank=True, related_name="positions", verbose_name="Оборудование")

    def __str__(self):
        return self.position_name

    class Meta:
        verbose_name = "Профессия/должность"
        verbose_name_plural = "Профессии/должности"