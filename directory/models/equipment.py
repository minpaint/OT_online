from django.db import models
from smart_selects.db_fields import ChainedForeignKey
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
    subdivision = ChainedForeignKey(
        StructuralSubdivision,
        chained_field="organization",
        chained_model_field="organization",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.CASCADE,
        related_name="equipment",
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
        on_delete=models.CASCADE,
        related_name="equipment",
        verbose_name="Отдел",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.equipment_name} (инв.№ {self.inventory_number})"

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"