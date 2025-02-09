from django.db import models


class Equipment(models.Model):
    """
    ⚙️ Модель для хранения оборудования.
    Оборудование привязано к организации, подразделению и отделу.
    """
    equipment_name = models.CharField("Наименование оборудования", max_length=255)
    inventory_number = models.CharField("Инвентарный номер", max_length=100, unique=True)
    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.CASCADE,
        related_name="equipment",
        verbose_name="Организация"
    )
    subdivision = models.ForeignKey(
        'directory.StructuralSubdivision',
        on_delete=models.CASCADE,
        verbose_name="Структурное подразделение",
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        'directory.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Отдел"
    )

    def __str__(self):
        return f"{self.equipment_name} (инв.№ {self.inventory_number})"

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
