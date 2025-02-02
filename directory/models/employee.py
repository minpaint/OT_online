from django.db import models
from smart_selects.db_fields import ChainedForeignKey
from .position import Position
from .organization import Organization
from .subdivision import StructuralSubdivision
from .department import Department

class Employee(models.Model):
    """Справочник: Сотрудники."""
    HEIGHT_CHOICES = [
        ("158-164 см", "158-164 см"),
        ("170-176 см", "170-176 см"),
        ("182-188 см", "182-188 см"),
        ("194-200 см", "194-200 см"),
    ]

    CLOTHING_SIZE_CHOICES = [
        ("44-46", "44-46"),
        ("48-50", "48-50"),
        ("52-54", "52-54"),
        ("56-58", "56-58"),
        ("60-62", "60-62"),
        ("64-66", "64-66"),
    ]

    SHOE_SIZE_CHOICES = [(str(i), str(i)) for i in range(36, 49)]

    # Основные поля
    full_name_nominative = models.CharField(
        max_length=255,
        verbose_name="ФИО (именительный)"
    )
    full_name_dative = models.CharField(
        max_length=255,
        verbose_name="ФИО (дательный)"
    )
    date_of_birth = models.DateField(verbose_name="Дата рождения")

    # Иерархия с необязательными полями subdivision и department
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name="Организация",
        related_name='employees'
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
        related_name='employees',
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
        verbose_name="Отдел",
        related_name='employees',
        null=True,
        blank=True
    )
    position = ChainedForeignKey(
        Position,
        chained_field="department",
        chained_model_field="department",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.PROTECT,
        verbose_name="Должность",
        related_name="employees",
        null=True,
        blank=True
    )

    # Остальные поля
    place_of_residence = models.TextField(verbose_name="Место проживания")
    height = models.CharField(
        max_length=15,
        choices=HEIGHT_CHOICES,
        blank=True,
        verbose_name="Рост"
    )
    clothing_size = models.CharField(
        max_length=5,
        choices=CLOTHING_SIZE_CHOICES,
        blank=True,
        verbose_name="Размер одежды"
    )
    shoe_size = models.CharField(
        max_length=2,
        choices=SHOE_SIZE_CHOICES,
        blank=True,
        verbose_name="Размер обуви"
    )
    is_contractor = models.BooleanField(
        default=False,
        verbose_name="Договор подряда"
    )

    def __str__(self):
        return self.full_name_nominative

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"