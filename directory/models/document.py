# directory/models/document.py
from django.db import models
from smart_selects.db_fields import ChainedForeignKey
from directory.models.organization import Organization
from directory.models.subdivision import StructuralSubdivision
from directory.models.department import Department

class Document(models.Model):
    name = models.CharField("Наименование документа", max_length=255)
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
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Отдел"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"