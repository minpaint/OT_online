from django.db import models
from smart_selects.db_fields import ChainedForeignKey
from .organization import Organization
from .subdivision import StructuralSubdivision
from .department import Department

class Document(models.Model):
    """Справочник: Документы (реестр документов)"""
    name = models.CharField(
        "Наименование документа",
        max_length=255
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="documents",
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
        related_name="documents",
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
        related_name="documents",
        verbose_name="Отдел",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name} ({self.organization.short_name_by})"

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"