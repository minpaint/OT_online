# 📁 directory/models/department.py
from django.db import models
from django.core.exceptions import ValidationError

class Department(models.Model):
    """Отдел – опциональный третий уровень иерархии."""
    name = models.CharField("Наименование", max_length=255)
    short_name = models.CharField("Сокращенное наименование", max_length=255, blank=True)

    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.PROTECT,
        related_name="departments",
        verbose_name="Организация"
    )

    subdivision = models.ForeignKey(
        'directory.StructuralSubdivision',
        on_delete=models.PROTECT,
        verbose_name="Структурное подразделение",
        related_name="departments"
    )

    def clean(self):
        if self.subdivision and self.subdivision.organization != self.organization:
            raise ValidationError({
                'subdivision': 'Подразделение должно принадлежать выбранной организации'
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.subdivision})"

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
        ordering = ['name']
        unique_together = ['name', 'subdivision']
