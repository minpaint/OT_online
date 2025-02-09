# 📁 directory/models/employee.py
from django.db import models
from django.core.exceptions import ValidationError

class Employee(models.Model):
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

    full_name_nominative = models.CharField(max_length=255, verbose_name="ФИО (именительный)")
    full_name_dative = models.CharField(max_length=255, verbose_name="ФИО (дательный)")
    date_of_birth = models.DateField(verbose_name="Дата рождения")
    place_of_residence = models.TextField(verbose_name="Место проживания")

    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.PROTECT,
        verbose_name="Организация",
        related_name='employees'
    )
    subdivision = models.ForeignKey(
        'directory.StructuralSubdivision',
        on_delete=models.PROTECT,
        verbose_name="Структурное подразделение",
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        'directory.Department',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Отдел"
    )
    position = models.ForeignKey(
        'directory.Position',
        on_delete=models.PROTECT,
        verbose_name="Должность"
    )

    height = models.CharField(max_length=15, choices=HEIGHT_CHOICES, blank=True, verbose_name="Рост")
    clothing_size = models.CharField(max_length=5, choices=CLOTHING_SIZE_CHOICES, blank=True, verbose_name="Размер одежды")
    shoe_size = models.CharField(max_length=2, choices=SHOE_SIZE_CHOICES, blank=True, verbose_name="Размер обуви")
    is_contractor = models.BooleanField(default=False, verbose_name="Договор подряда")

    def clean(self):
        if self.department and not self.subdivision:
            raise ValidationError({'department': 'Нельзя указать отдел без структурного подразделения'})
        if self.position:
            if self.department:
                if self.position.department and self.position.department != self.department:
                    raise ValidationError({'position': 'Выбранная должность не соответствует указанному отделу'})
            elif self.subdivision:
                if self.position.subdivision and self.position.subdivision != self.subdivision:
                    raise ValidationError({'position': 'Выбранная должность не соответствует указанному подразделению'})
            if self.position.organization != self.organization:
                raise ValidationError({'position': 'Выбранная должность не принадлежит указанной организации'})
        if self.subdivision and self.subdivision.organization != self.organization:
            raise ValidationError({'subdivision': 'Выбранное подразделение не принадлежит указанной организации'})
        if self.department and self.department.subdivision != self.subdivision:
            raise ValidationError({'department': 'Выбранный отдел не принадлежит указанному подразделению'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        parts = [self.full_name_nominative]
        if self.position:
            parts.append(f"- {self.position}")
        return " ".join(parts)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['full_name_nominative']
