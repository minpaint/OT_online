from django.db import models

class Organization(models.Model):
    """Справочник: Организации."""
    full_name_ru = models.CharField(max_length=255, verbose_name="Полное наименование (рус)")
    short_name_ru = models.CharField(max_length=255, verbose_name="Сокращенное наименование (рус)", blank=True)
    requisites_ru = models.TextField(verbose_name="Реквизиты (рус)")
    full_name_by = models.CharField(max_length=255, verbose_name="Полное наименование (бел)")
    short_name_by = models.CharField(max_length=255, verbose_name="Сокращенное наименование (бел)", blank=True)
    requisites_by = models.TextField(verbose_name="Реквизиты (бел)")

    def __str__(self):
        return self.full_name_ru

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"

