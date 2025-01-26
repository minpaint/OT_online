from django.db import models

class Document(models.Model):
    """Справочник: Документы (реестр документов)."""
    name = models.CharField(max_length=255, verbose_name="Наименование документа")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
