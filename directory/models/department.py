from django.db import models
from .organization import Organization
from .subdivision import StructuralSubdivision
from smart_selects.db_fields import ChainedForeignKey

class Department(models.Model):
    """Отдел – опциональный третий уровень иерархии."""
    name = models.CharField("Наименование", max_length=255)
    short_name = models.CharField("Сокращенное наименование", max_length=255, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="departments",  # Обратная связь: instance.departments
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
        related_name="departments"  # Обязательно: обратная связь от структурного подразделения к отделам
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
