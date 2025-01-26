from django.db import models
from .organization import Organization

class StructuralSubdivision(models.Model):
    """Справочник: Структурные подразделения."""
    name = models.CharField(max_length=255, verbose_name="Наименование")
    short_name = models.CharField(max_length=255, blank=True, verbose_name="Сокращенное наименование")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="subdivisions", verbose_name="Организация")
    parent_subdivision = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_subdivisions', verbose_name="Родительское подразделение")

    def __str__(self):
        return f"{self.name} ({self.organization.full_name_ru})"

    class Meta:
        verbose_name = "Структурное подразделение"
        verbose_name_plural = "Структурные подразделения"
