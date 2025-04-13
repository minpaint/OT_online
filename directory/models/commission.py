# directory/models/commission.py

from django.db import models
from django.core.exceptions import ValidationError


class Commission(models.Model):
    """
    🔍 Модель для хранения комиссий по проверке знаний ОТ.
    Комиссии могут быть привязаны к организации, подразделению или отделу.
    """
    COMMISSION_TYPES = [
        ('ot', '🛡️ Охрана труда'),
        ('eb', '⚡ Электробезопасность'),
        ('pb', '🔥 Пожарная безопасность'),
        ('other', '📋 Иная'),
    ]

    name = models.CharField('Наименование комиссии', max_length=255)
    commission_type = models.CharField(
        'Тип комиссии',
        max_length=10,
        choices=COMMISSION_TYPES,
        default='ot'
    )
    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.CASCADE,
        related_name='commissions',
        verbose_name='Организация',
        blank=True,
        null=True
    )
    subdivision = models.ForeignKey(
        'directory.StructuralSubdivision',
        on_delete=models.CASCADE,
        related_name='commissions',
        verbose_name='Структурное подразделение',
        blank=True,
        null=True
    )
    department = models.ForeignKey(
        'directory.Department',
        on_delete=models.CASCADE,
        related_name='commissions',
        verbose_name='Отдел',
        blank=True,
        null=True
    )
    is_active = models.BooleanField('Активна', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Комиссия по проверке знаний'
        verbose_name_plural = 'Комиссии по проверке знаний'
        ordering = ['-is_active', 'name']

    def __str__(self):
        return self.name

    def clean(self):
        """Валидация модели при сохранении"""
        # Проверка на наличие только одной привязки
        bindings = sum(1 for field in [self.department, self.subdivision, self.organization] if field is not None)
        if bindings != 1:
            raise ValidationError(
                'Комиссия должна быть привязана только к одному уровню: организация, '
                'структурное подразделение или отдел.'
            )

    def get_level_display(self):
        """Возвращает текстовое представление уровня комиссии"""
        if self.department:
            return f"Уровень отдела: {self.department.name}"
        elif self.subdivision:
            return f"Уровень подразделения: {self.subdivision.name}"
        elif self.organization:
            return f"Уровень организации: {self.organization.short_name_ru}"
        return "Уровень не определен"


class CommissionMember(models.Model):
    """
    👤 Модель для хранения участников комиссии с указанием роли.
    """
    ROLE_CHOICES = [
        ('chairman', '👑 Председатель комиссии'),
        ('member', '👤 Член комиссии'),
        ('secretary', '📝 Секретарь комиссии'),
    ]

    commission = models.ForeignKey(
        Commission,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='Комиссия'
    )
    employee = models.ForeignKey(
        'directory.Employee',
        on_delete=models.CASCADE,
        related_name='commission_roles',
        verbose_name='Сотрудник'
    )
    role = models.CharField(
        'Роль в комиссии',
        max_length=10,
        choices=ROLE_CHOICES,
        default='member'
    )
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Участник комиссии'
        verbose_name_plural = 'Участники комиссии'
        ordering = ['role', 'employee__full_name_nominative']
        unique_together = ['commission', 'employee', 'role']

    def __str__(self):
        return f"{self.get_role_display()}: {self.employee.full_name_nominative}"

    def clean(self):
        """Валидация модели при сохранении"""
        # Проверяем, что для ролей 'chairman' и 'secretary' есть только один активный участник
        if self.is_active and self.role in ['chairman', 'secretary']:
            existing = CommissionMember.objects.filter(
                commission=self.commission,
                role=self.role,
                is_active=True
            ).exclude(id=self.id)

            if existing.exists():
                role_display = dict(self.ROLE_CHOICES)[self.role]
                raise ValidationError(
                    f'В комиссии уже есть активный {role_display.lower()}. '
                    'Пожалуйста, деактивируйте его перед назначением нового.'
                )