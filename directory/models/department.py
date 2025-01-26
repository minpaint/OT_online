from django.db import models
from .organization import Organization
from .subdivision import StructuralSubdivision

class Department(models.Model):
    """Справочник: Отделы."""
    name = models.CharField(max_length=255, verbose_name="Наименование")
    short_name = models.CharField(max_length=255, blank=True, verbose_name="Сокращенное наименование")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="departments", verbose_name="Организация")
    subdivision = models.ForeignKey(StructuralSubdivision, on_delete=models.SET_NULL, null=True, blank=True, related_name="departments", verbose_name="Структурное подразделение")

    def __str__(self):
        return f"{self.name} ({self.organization.full_name_ru})"

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
