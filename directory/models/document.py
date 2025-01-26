from django.db import models
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
    subdivision = models.ForeignKey(
        StructuralSubdivision,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Структурное подразделение"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name="Отдел"
    )

    def __str__(self):
        return f"{self.name} ({self.organization.short_name_by})"

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
