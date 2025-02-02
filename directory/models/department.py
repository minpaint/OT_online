from django.db import models
from smart_selects.db_fields import ChainedForeignKey
from .organization import Organization
from .subdivision import StructuralSubdivision

class Department(models.Model):
    """Отдел – опциональный третий уровень иерархии."""
    name = models.CharField("Наименование", max_length=255)
    short_name = models.CharField("Сокращенное наименование", max_length=255, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="departments",
        verbose_name="Организация"
    )
    subdivision = ChainedForeignKey(
        StructuralSubdivision,
        chained_field="organization",
        chained_model_field="organization",
        show_all=False,
        auto_choose=True,
        sort=True,
        verbose_name="Структурное подразделение",
        related_name="departments"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
