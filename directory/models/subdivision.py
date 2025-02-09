# 📁 directory/models/subdivision.py
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

class StructuralSubdivision(MPTTModel):
    """Структурное подразделение - второй уровень иерархии"""
    name = models.CharField("Наименование", max_length=255)
    short_name = models.CharField("Сокращенное наименование", max_length=255, blank=True)
    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.PROTECT,
        related_name="subdivisions",
        verbose_name="Организация"
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительское подразделение"
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return f"{self.name} ({self.organization.short_name_ru or self.organization.full_name_ru})"

    class Meta:
        verbose_name = "Структурное подразделение"
        verbose_name_plural = "Структурные подразделения"
        ordering = ['name']
