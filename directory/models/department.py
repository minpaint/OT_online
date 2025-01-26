from django.db import models
from .organization import Organization
from .subdivision import StructuralSubdivision

class Department(models.Model):
    """Отдел - опциональный третий уровень иерархии"""
    name = models.CharField("Наименование", max_length=255)
    short_name = models.CharField("Сокращенное наименование", max_length=255, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="departments",
        verbose_name="Организация"
    )
    subdivision = models.ForeignKey(
        StructuralSubdivision,
        on_delete=models.CASCADE,  # Если удаляем подразделение, удаляем и отделы
        related_name="departments",
        verbose_name="Структурное подразделение"
    )

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"