# deadline_control/context_processors/notifications.py
from django.utils import timezone
from datetime import timedelta
from deadline_control.models import Equipment, KeyDeadlineItem
from deadline_control.models.medical_norm import EmployeeMedicalExamination
from directory.utils.permissions import AccessControlHelper


def deadline_notifications(request):
    """
    Context processor для отображения уведомлений об истекающих сроках
    """
    if not request.user.is_authenticated:
        return {}

    today = timezone.now().date()
    warning_date = today + timedelta(days=7)  # Уведомления за 7 дней

    # Фильтрация по организациям пользователя через AccessControlHelper
    allowed_orgs = AccessControlHelper.get_accessible_organizations(request.user, request)

    # Подсчёт просроченного оборудования
    equipment_qs = Equipment.objects.filter(organization__in=allowed_orgs)

    overdue_equipment_count = 0
    upcoming_equipment_count = 0

    for eq in equipment_qs:
        if eq.next_maintenance_date:
            if eq.next_maintenance_date < today:
                overdue_equipment_count += 1
            elif eq.next_maintenance_date <= warning_date:
                upcoming_equipment_count += 1

    # Подсчёт просроченных мероприятий
    deadlines_qs = KeyDeadlineItem.objects.select_related('category').filter(
        category__organization__in=allowed_orgs,
        category__is_active=True
    )

    overdue_deadlines_count = 0
    upcoming_deadlines_count = 0

    for item in deadlines_qs:
        if item.next_date:
            if item.next_date < today:
                overdue_deadlines_count += 1
            elif item.next_date <= warning_date:
                upcoming_deadlines_count += 1

    # Подсчёт просроченных медосмотров
    medical_qs = EmployeeMedicalExamination.objects.select_related('employee').filter(
        employee__organization__in=allowed_orgs
    )

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
