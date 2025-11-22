# 📁 directory/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from directory.models import Employee, Position, StructuralSubdivision, Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Автоматически создаёт Profile для нового пользователя.
    """
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Position)
def update_employee_subdivision(sender, instance, **kwargs):
    """
    Обновляет подразделение у сотрудников при изменении подразделения должности.
    Если у должности указано подразделение, сотрудники с данной позицией и незаполненным полем subdivision получают это значение.
    """
    if instance.subdivision:
        Employee.objects.filter(position=instance, subdivision__isnull=True).update(subdivision=instance.subdivision)

@receiver(post_save, sender=StructuralSubdivision)
def update_departments(sender, instance, **kwargs):
    """
    Обновляет организацию в отделах при изменении организации подразделения.
    """
    if hasattr(instance, 'departments'):
        instance.departments.all().update(organization=instance.organization)
    else:
        instance.department_set.all().update(organization=instance.organization)


@receiver(pre_save, sender=Employee)
def cache_old_position(sender, instance, **kwargs):
    """
    Кэширует старую должность сотрудника перед сохранением,
    чтобы в post_save можно было определить, изменилась ли она.
    """
    if instance.pk:
        try:
            # Сохраняем старую должность в самом объекте instance
            instance._old_position = Employee.objects.get(pk=instance.pk).position
        except Employee.DoesNotExist:
            instance._old_position = None
    else:
        # Для нового сотрудника старой должности нет
        instance._old_position = None


def get_harmful_factors_for_position(position):
    """
    Получает список вредных факторов для должности с учетом иерархии:
    1. PositionMedicalFactor (переопределения для конкретной должности)
    2. MedicalExaminationNorm (эталонные нормы по названию профессии)

    Returns:
        QuerySet[HarmfulFactor]
    """
    from deadline_control.models import MedicalExaminationNorm, HarmfulFactor

    if not position:
        return HarmfulFactor.objects.none()

    # Проверяем переопределения для конкретной должности
    position_factors = position.medical_factors.filter(is_disabled=False).select_related('harmful_factor')

    if position_factors.exists():
        # Используем переопределённые факторы
        return HarmfulFactor.objects.filter(
            id__in=position_factors.values_list('harmful_factor_id', flat=True)
        )
    else:
        # Если переопределений нет - берём эталонные нормы по названию должности
        reference_norms = MedicalExaminationNorm.objects.filter(
            position_name=position.position_name
        ).select_related('harmful_factor')

        return HarmfulFactor.objects.filter(
            id__in=reference_norms.values_list('harmful_factor_id', flat=True)
        )


@receiver(post_save, sender=Employee)
def update_medical_examinations_on_change(sender, instance, created, **kwargs):
    """
    Автоматически создает или обновляет записи медосмотров при создании
    или изменении должности сотрудника.

    Учитывает иерархию: PositionMedicalFactor → MedicalExaminationNorm
    """
    # Импортируем здесь, чтобы избежать циклических импортов
    from deadline_control.models import EmployeeMedicalExamination

    if created:
        # --- Логика для НОВОГО сотрудника ---
        if instance.position:
            harmful_factors = get_harmful_factors_for_position(instance.position)
            for factor in harmful_factors:
                EmployeeMedicalExamination.objects.get_or_create(
                    employee=instance,
                    harmful_factor=factor,
                )
    elif hasattr(instance, '_old_position') and instance._old_position != instance.position:
        # --- Логика для ИЗМЕНЕНИЯ ДОЛЖНОСТИ ---
        old_position = instance._old_position
        new_position = instance.position

        # Получаем наборы ID вредных факторов с учетом иерархии
        old_factor_ids = set()
        if old_position:
            old_factors = get_harmful_factors_for_position(old_position)
            old_factor_ids = set(old_factors.values_list('id', flat=True))

        new_factor_ids = set()
        if new_position:
            new_factors = get_harmful_factors_for_position(new_position)
            new_factor_ids = set(new_factors.values_list('id', flat=True))

        # Находим факторы, которые нужно добавить
        factors_to_add_ids = new_factor_ids - old_factor_ids

        if factors_to_add_ids:
            from deadline_control.models.medical_examination import HarmfulFactor
            factors_to_add = HarmfulFactor.objects.filter(pk__in=factors_to_add_ids)
            for factor in factors_to_add:
                # Создаем только если такого медосмотра еще нет (на всякий случай)
                EmployeeMedicalExamination.objects.get_or_create(
                    employee=instance,
                    harmful_factor=factor,
                )

        # Факторы, которые были в старой должности, но нет в новой, мы не трогаем.
        # Логика их фильтрации теперь лежит в методе Employee.get_medical_status(),
        # который учитывает только факторы ТЕКУЩЕЙ должности.
