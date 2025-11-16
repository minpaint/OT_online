# deadline_control/context_processors/notifications.py
from django.utils import timezone
from datetime import timedelta
from deadline_control.models import Equipment, KeyDeadlineItem
from directory.models import EmployeeMedicalExamination


def deadline_notifications(request):
    """
    Context processor для отображения уведомлений об истекающих сроках
    """
    if not request.user.is_authenticated:
        return {}

    today = timezone.now().date()
    warning_date = today + timedelta(days=7)  # Уведомления за 7 дней

    # Фильтрация по организациям пользователя
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        allowed_orgs = request.user.profile.organizations.all()
    else:
        allowed_orgs = None

    # Подсчёт просроченного оборудования
    equipment_qs = Equipment.objects.all()
    if allowed_orgs:
        equipment_qs = equipment_qs.filter(organization__in=allowed_orgs)

    overdue_equipment_count = 0
    upcoming_equipment_count = 0

    for eq in equipment_qs:
        if eq.next_maintenance_date:
            if eq.next_maintenance_date < today:
                overdue_equipment_count += 1
            elif eq.next_maintenance_date <= warning_date:
                upcoming_equipment_count += 1

    # Подсчёт просроченных мероприятий
    deadlines_qs = KeyDeadlineItem.objects.select_related('category')
    if allowed_orgs:
        deadlines_qs = deadlines_qs.filter(category__organization__in=allowed_orgs, category__is_active=True)

    overdue_deadlines_count = 0
    upcoming_deadlines_count = 0

    for item in deadlines_qs:
        if item.next_date:
            if item.next_date < today:
                overdue_deadlines_count += 1
            elif item.next_date <= warning_date:
                upcoming_deadlines_count += 1

    # Подсчёт просроченных медосмотров
    medical_qs = EmployeeMedicalExamination.objects.select_related('employee')
    if allowed_orgs:
        medical_qs = medical_qs.filter(employee__organization__in=allowed_orgs)

    overdue_medical_count = 0
    upcoming_medical_count = 0

    for exam in medical_qs:
        if exam.next_date:
            if exam.next_date < today:
                overdue_medical_count += 1
            elif exam.next_date <= warning_date:
                upcoming_medical_count += 1

    return {
        'deadline_overdue_total': overdue_equipment_count + overdue_deadlines_count + overdue_medical_count,
        'deadline_upcoming_total': upcoming_equipment_count + upcoming_deadlines_count + upcoming_medical_count,
        'deadline_notifications_count': overdue_equipment_count + overdue_deadlines_count + upcoming_equipment_count + upcoming_deadlines_count + overdue_medical_count + upcoming_medical_count,
    }
