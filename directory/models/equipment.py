from django.db import models
from .organization import Organization
from .subdivision import StructuralSubdivision

class Equipment(models.Model):
    """Справочник: Оборудование."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="equipment", verbose_name="Организация")
    subdivision = models.ForeignKey(StructuralSubdivision, on_delete=models.SET_NULL, null=True, blank=True, related_name="equipment", verbose_name="Структурное подразделение")
    equipment_name = models.CharField(max_length=255, verbose_name="Наименование оборудования")
    inventory_number = models.CharField(max_length=100, unique=True, verbose_name="Инвентарный номер")

    def __str__(self):
        return f"{self.equipment_name} (инв.№ {self.inventory_number})"

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
