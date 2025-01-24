from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from .base import BaseModel
from .position import Position


class Employee(BaseModel):
    """Сотрудники"""
    # ФИО (два поля)
    full_name = models.CharField(
        'ФИО в именительном падеже',
        max_length=300,
        help_text='Например: "Иванов Иван Иванович"'
    )
    full_name_dative = models.CharField(
        'ФИО в дательном падеже',
        max_length=300,
        help_text='Например: "Иванову Ивану Ивановичу"'
    )

    # Размеры одежды и обуви
    CLOTHING_SIZES = [
        ('44-46', '44-46'),
        ('48-50', '48-50'),
        ('52-54', '52-54'),
        ('56-58', '56-58'),
        ('60-62', '60-62'),
        ('64-66', '64-66'),
    ]

    HEIGHT_RANGES = [
        ('158-164', '158-164 см'),
        ('170-176', '170-176 см'),
        ('182-188', '182-188 см'),
        ('194-200', '194-200 см'),
    ]

    SHOE_SIZES = [(i, str(i)) for i in range(36, 49)]

    # Основные данные
    birth_date = models.DateField('Дата рождения')
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        verbose_name='Должность'
    )

    # Контактные данные
    phone = models.CharField(
        'Телефон',
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Номер телефона должен быть введен в формате: "+999999999".'
            )
        ]
    )
    email = models.EmailField(
        'Email',
        validators=[EmailValidator()]
    )

    # Антропометрические данные
    height = models.CharField(
        'Рост',
        max_length=10,
        choices=HEIGHT_RANGES
    )
    clothing_size = models.CharField(
        'Размер одежды',
        max_length=10,
        choices=CLOTHING_SIZES
    )
    shoe_size = models.IntegerField(
        'Размер обуви',
        choices=SHOE_SIZES
    )

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} - {self.position}"

    @property
    def organizational_unit(self):
        """Получить подразделение сотрудника через должность"""
        return self.position.organizational_unit if self.position else None

    def get_manager(self):
        """Получить руководителя подразделения"""
        unit = self.organizational_unit
        if unit:
            # Получаем руководящие должности в родительском подразделении
            parent_unit = unit.parent
            if parent_unit:
                return Employee.objects.filter(
                    position__organizational_unit=parent_unit
                ).first()
        return None

    def get_colleagues(self):
        """Получить коллег (сотрудников того же подразделения)"""
        if self.organizational_unit:
            return Employee.objects.filter(
                position__organizational_unit=self.organizational_unit
            ).exclude(id=self.id)
        return Employee.objects.none()