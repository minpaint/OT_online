from django.db import models

class StructuralSubdivision(models.Model):
    """Структурное подразделение - второй уровень иерархии"""
    name = models.CharField("Наименование", max_length=255)
    short_name = models.CharField("Сокращенное наименование", max_length=255, blank=True)
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.PROTECT,
        related_name="subdivisions",
        verbose_name="Организация"
    )

    def __str__(self):
        return f"{self.name} ({self.organization.short_name_ru or self.organization.full_name_ru})"

    class Meta:
        verbose_name = "Структурное подразделение"
        verbose_name_plural = "Структурные подразделения"
        ordering = ['name']