from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class EmployeeQuerySet(models.QuerySet):
    def tree_visible(self):
        """Сотрудники, которые должны отображаться в древе (исключая кандидатов и уволенных)"""
        return self.exclude(status__in=['candidate', 'fired'])
    def candidates(self):
        """Только кандидаты"""
        return self.filter(status='candidate')

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

    # Типы договоров
    CONTRACT_TYPE_CHOICES = [
        ('standard', 'Трудовой договор'),
        ('contractor', 'Договор подряда'),
        ('part_time', 'Совмещение'),
        ('transfer', 'Перевод'),
        ('return', 'Выход из ДО'),
    ]

    # Статус сотрудника
    EMPLOYEE_STATUS_CHOICES = [
        ('candidate', 'Кандидат'),
        ('active', 'Оформлен'),
        ('maternity_leave', 'В декретном отпуске'),
        ('part_time', 'Совместитель'),
        ('fired', 'Уволен'),
    ]

    full_name_nominative = models.CharField(
        max_length=255,
        verbose_name="ФИО"
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
    contract_type = models.CharField(
        verbose_name="Вид договора",
        max_length=20,
        choices=CONTRACT_TYPE_CHOICES,
        default='standard'
    )
    # ✅ Новое поле статуса сотрудника
    status = models.CharField(
        verbose_name="Статус сотрудника",
        max_length=20,
        choices=EMPLOYEE_STATUS_CHOICES,
        default='active',
        db_index=True,
        help_text="Текущий статус сотрудника в организации"
    )
    hire_date = models.DateField(
        verbose_name="Дата приема",
        default=timezone.now
    )
    start_date = models.DateField(
        verbose_name="Дата начала работы",
        default=timezone.now
    )
    is_contractor = models.BooleanField(
        default=False,
        verbose_name="Договор подряда",
        help_text="Устаревшее поле, используйте contract_type"
    )

    objects = EmployeeQuerySet.as_manager()

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ['full_name_nominative']

    def clean(self):
        """Валидация соответствия организации, подразделения, отдела и должности."""
        if self.position.organization != self.organization:
            raise ValidationError({
                'position': 'Должность должна принадлежать выбранной организации'
            })
        if self.subdivision:
            if self.subdivision.organization != self.organization:
                raise ValidationError({
                    'subdivision': 'Подразделение должно принадлежать выбранной организации'
                })
            if self.position.subdivision and self.position.subdivision != self.subdivision:
                raise ValidationError({
                    'position': 'Должность должна соответствовать выбранному подразделению'
                })
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
        self.clean()
        super().save(*args, **kwargs)

    def get_status_display_emoji(self):
        """Возвращает статус с эмодзи для наглядности в интерфейсе"""
        status_emojis = {
            'candidate': '📝',
            'active': '✅',
            'maternity_leave': '👶',
            'part_time': '⌛',
            'fired': '🚫',
        }
        emoji = status_emojis.get(self.status, '')
        return f"{emoji} {self.get_status_display()}"

    def get_contract_type_display(self):
        """Возвращает человекопонятное название типа договора"""
        return dict(self.CONTRACT_TYPE_CHOICES).get(self.contract_type, "Неизвестно")

    @property
    def name_with_position(self):
        """👷 Возвращает строку "ФИО (именительный) – Название должности"."""
        if self.position:
            return f"{self.full_name_nominative} — {self.position}"
        return self.full_name_nominative

    def get_medical_status(self):
        """
        🏥 Возвращает статус медицинских осмотров сотрудника.

        Логика:
        - Получает вредные факторы с учетом иерархии (PositionMedicalFactor → MedicalExaminationNorm)
        - Находит минимальную периодичность среди всех вредных факторов
        - Рассчитывает следующую дату медосмотра на основе минимальной периодичности
        - Определяет статус (no_date, expired, upcoming, normal)

        Returns:
            dict или None: Словарь с информацией о статусе медосмотра или None, если медосмотров нет
            {
                'has_date': bool,  # Есть ли дата медосмотра
                'date_completed': date или None,  # Дата последнего медосмотра
                'next_date': date или None,  # Дата следующего медосмотра
                'min_periodicity': int или None,  # Минимальная периодичность в месяцах
                'days_until': int или None,  # Дней до следующего медосмотра (может быть отрицательным)
                'status': str,  # no_date, expired, upcoming, normal
                'factors': list,  # Список вредных факторов
            }
        """
        from deadline_control.models import EmployeeMedicalExamination, MedicalExaminationNorm
        from django.utils import timezone

        # Проверяем наличие должности
        if not self.position:
            return None

        # ШАГИ 1-2: Получаем вредные факторы с учетом иерархии
        # 1. Проверяем переопределения для конкретной должности (PositionMedicalFactor)
        position_factors = self.position.medical_factors.filter(is_disabled=False).select_related('harmful_factor')

        harmful_factors = []
        if position_factors.exists():
            # Используем переопределённые факторы
            harmful_factors = [pf.harmful_factor for pf in position_factors]
        else:
            # 2. Если переопределений нет - берём эталонные нормы по названию должности
            reference_norms = MedicalExaminationNorm.objects.filter(
                position_name=self.position.position_name
            ).select_related('harmful_factor')
            harmful_factors = [norm.harmful_factor for norm in reference_norms]

        # Если вообще нет факторов - медосмотры не требуются
        if not harmful_factors:
            return None

        # ШАГ 3: Получаем записи медосмотров для этих факторов (только активные)
        harmful_factor_ids = [f.id for f in harmful_factors]
        examinations = self.medical_examinations.filter(
            harmful_factor_id__in=harmful_factor_ids,
            is_disabled=False  # Игнорируем отключенные медосмотры
        ).select_related('harmful_factor')

        # ШАГ 4: Собираем информацию о факторах и датах
        factors = []
        min_periodicity = None
        has_date = False
        earliest_date = None

        # Если записей медосмотров нет - используем факторы напрямую
        if not examinations.exists():
            for factor in harmful_factors:
                factors.append({
                    'name': factor.full_name,
                    'short_name': factor.short_name,
                    'periodicity': factor.periodicity,
                })
                if min_periodicity is None or factor.periodicity < min_periodicity:
                    min_periodicity = factor.periodicity

            # Возвращаем статус "нужно внести дату"
            return {
                'has_date': False,
                'date_completed': None,
                'next_date': None,
                'min_periodicity': min_periodicity,
                'days_until': None,
                'status': 'no_date',
                'factors': factors,
            }

        # Если записи есть - анализируем их
        exams_without_date = []
        for exam in examinations:
            factors.append({
                'name': exam.harmful_factor.full_name,
                'short_name': exam.harmful_factor.short_name,
                'periodicity': exam.harmful_factor.periodicity,
            })

            # Находим минимальную периодичность
            if min_periodicity is None or exam.harmful_factor.periodicity < min_periodicity:
                min_periodicity = exam.harmful_factor.periodicity

            # Проверяем, есть ли дата
            if exam.date_completed:
                has_date = True
                if earliest_date is None or exam.date_completed < earliest_date:
                    earliest_date = exam.date_completed
            else:
                exams_without_date.append(exam)

        # Если нет ни одной даты - статус "нужно внести дату"
        if not has_date:
            return {
                'has_date': False,
                'date_completed': None,
                'next_date': None,
                'min_periodicity': min_periodicity,
                'days_until': None,
                'status': 'no_date',
                'factors': factors,
                'exams_without_date_count': len(exams_without_date),
            }

        # Рассчитываем следующую дату на основе минимальной периодичности
        from deadline_control.models.medical_norm import EmployeeMedicalExamination as MedExamModel
        next_date = MedExamModel._add_months(earliest_date, min_periodicity)

        # Рассчитываем дни до следующего медосмотра
        today = timezone.now().date()
        days_until = (next_date - today).days

        # Определяем статус
        if days_until < 0:
            status = 'expired'
        elif days_until <= 30:
            status = 'upcoming'
        else:
            status = 'normal'

        return {
            'has_date': True,
            'date_completed': earliest_date,
            'next_date': next_date,
            'min_periodicity': min_periodicity,
            'days_until': days_until,
            'status': status,
            'factors': factors,
            'exams_without_date_count': len(exams_without_date),
        }

    def __str__(self):
        parts = [self.full_name_nominative, "-", str(self.position)]
        return " ".join(parts)

    def tree_display_name(self):
        """👤 Отображение имени сотрудника в древовидной структуре."""
        return f"{self.full_name_nominative} — {self.position.position_name}"