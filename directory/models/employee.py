from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Employee(models.Model):
    """
    👤 Модель для хранения информации о сотрудниках.
    """
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

    # Добавляем константы для типов договоров
    CONTRACT_TYPE_CHOICES = [
        ('standard', 'Трудовой договор'),
        ('contractor', 'Договор подряда'),
        ('part_time', 'Совмещение'),
        ('transfer', 'Перевод'),
        ('return', 'Выход из ДО'),
    ]

    full_name_nominative = models.CharField(
        max_length=255,
        verbose_name="ФИО (именительный)"
    )
    full_name_dative = models.CharField(
        max_length=255,
        verbose_name="ФИО (дательный)"
    )
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
        blank=True,
        related_name='employees'
    )
    department = models.ForeignKey(
        'directory.Department',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Отдел",
        related_name='employees'
    )
    position = models.ForeignKey(
        'directory.Position',
        on_delete=models.PROTECT,
        verbose_name="Должность"
    )

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

    # Заменяем булево поле на поле с выбором типа договора
    contract_type = models.CharField(
        verbose_name="Вид договора",
        max_length=20,
        choices=CONTRACT_TYPE_CHOICES,
        default='standard'
    )

    # Новые поля для дат
    hire_date = models.DateField(
        verbose_name="Дата приема",
        default=timezone.now
    )
    start_date = models.DateField(
        verbose_name="Дата начала работы",
        default=timezone.now
    )

    # Сохраняем поле is_contractor для обратной совместимости
    # Будем заполнять его автоматически на основе contract_type
    is_contractor = models.BooleanField(
        default=False,
        verbose_name="Договор подряда",
        help_text="Устаревшее поле, используйте contract_type"
    )

    def clean(self):
        """
        Валидация соответствия организации, подразделения, отдела и должности.
        """
        # Проверка, что должность принадлежит выбранной организации
        if self.position.organization != self.organization:
            raise ValidationError({
                'position': 'Должность должна принадлежать выбранной организации'
            })

        # Проверка подразделения
        if self.subdivision:
            if self.subdivision.organization != self.organization:
                raise ValidationError({
                    'subdivision': 'Подразделение должно принадлежать выбранной организации'
                })
            if self.position.subdivision and self.position.subdivision != self.subdivision:
                raise ValidationError({
                    'position': 'Должность должна соответствовать выбранному подразделению'
                })

        # Проверка отдела
        if self.department:
            if not self.subdivision:
                raise ValidationError({
                    'department': 'Нельзя указать отдел без структурного подразделения'
                })
            if self.department.organization != self.organization:
                raise ValidationError({
                    'department': 'Отдел должен принадлежать выбранной организации'
                })
            if self.department.subdivision != self.subdivision:
                raise ValidationError({
                    'department': 'Отдел должен принадлежать выбранному подразделению'
                })
            if self.position.department and self.position.department != self.department:
                raise ValidationError({
                    'position': 'Должность должна соответствовать выбранному отделу'
                })

    def save(self, *args, **kwargs):
        # Синхронизация is_contractor с contract_type для обратной совместимости
        self.is_contractor = (self.contract_type == 'contractor')

        # При необходимости, автоматическое заполнение full_name_dative (не делаем здесь,
        # так как для этого используем pymorphy2 в другом месте)

        self.clean()
        super().save(*args, **kwargs)

    def get_contract_type_display(self):
        """Возвращает человекопонятное название типа договора"""
        return dict(self.CONTRACT_TYPE_CHOICES).get(self.contract_type, "Неизвестно")

    @property
    def name_with_position(self):
        """
        👷 Возвращаем строку "ФИО (именительный) – Название должности".
        Если должность не указана (маловероятно), просто ФИО.
        """
        if self.position:
            return f"{self.full_name_nominative} — {self.position}"
        return self.full_name_nominative

    def __str__(self):
        # По умолчанию __str__ оставляем старый вариант: "ФИО - Должность"
        parts = [self.full_name_nominative, "-", str(self.position)]
        return " ".join(parts)

    def tree_display_name(self):
        """
        👤 Метод для отображения имени сотрудника в древовидной структуре
        без избыточной информации в скобках.
        """
        return f"{self.full_name_nominative} — {self.position.position_name}"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['full_name_nominative']