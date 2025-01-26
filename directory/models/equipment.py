from django.db import models
from .organization import Organization
from .subdivision import StructuralSubdivision
from .department import Department

class Equipment(models.Model):
    """Справочник: Оборудование"""
    equipment_name = models.CharField(
        "Наименование оборудования",
        max_length=255
    )
    inventory_number = models.CharField(
        "Инвентарный номер",
        max_length=100,
        unique=True
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="equipment",
        verbose_name="Организация"
    )
    subdivision = models.ForeignKey(
        StructuralSubdivision,
        on_delete=models.CASCADE,
        related_name="equipment",
        verbose_name="Структурное подразделение"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipment",
        verbose_name="Отдел"
    )

    def __str__(self):
        return f"{self.equipment_name} (инв.№ {self.inventory_number})"

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"