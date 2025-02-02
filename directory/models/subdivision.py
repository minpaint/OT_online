from django.db import models
from .organization import Organization

class StructuralSubdivision(models.Model):
    """Структурное подразделение - второй уровень иерархии"""
    name = models.CharField("Наименование", max_length=255)
    short_name = models.CharField("Сокращенное наименование", max_length=255, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="subdivisions",
        verbose_name="Организация"
    )

    class Meta:
        verbose_name = "Структурное подразделение"
        verbose_name_plural = "Структурные подразделения"

    def __str__(self):
        return f"{self.name} ({self.organization.full_name_ru})"
