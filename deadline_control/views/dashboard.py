# deadline_control/views/dashboard.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from deadline_control.models import Equipment, KeyDeadlineCategory, KeyDeadlineItem
from deadline_control.models.medical_norm import EmployeeMedicalExamination
from directory.utils.permissions import AccessControlHelper


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Главная страница приложения Контроль сроков с обзором всех истекающих сроков
    """
    template_name = 'deadline_control/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        today = timezone.now().date()
        warning_date = today + timedelta(days=14)

        # Получаем доступные организации через AccessControlHelper
        accessible_orgs = AccessControlHelper.get_accessible_organizations(user, self.request)

        # Фильтр по конкретной организации из GET-параметра
        org_id = self.request.GET.get('org')
        selected_org = None
        if org_id:
            from directory.models import Organization
            try:
                selected_org = Organization.objects.get(pk=org_id)
                # ВАЖНО: Проверяем права доступа через AccessControlHelper
                if not user.is_superuser and selected_org not in accessible_orgs:
                    # Пользователь пытается получить доступ к организации, к которой у него нет прав
                    selected_org = None
                else:
                    context['selected_org'] = selected_org
            except Organization.DoesNotExist:
                pass

        # ========== ОБОРУДОВАНИЕ ==========
        equipment_qs = Equipment.objects.select_related('organization', 'subdivision', 'department')

        # КРИТИЧНО: Применяем фильтрацию по правам ВСЕГДА через AccessControlHelper
        equipment_qs = AccessControlHelper.filter_queryset(equipment_qs, user, self.request)

        # Дополнительная фильтрация по выбранной организации (если указана)
        if selected_org:
            equipment_qs = equipment_qs.filter(organization=selected_org)

        # Просроченное ТО
        overdue_equipment = []
        # Скоро ТО (в течение 14 дней)
        upcoming_equipment = []

        for eq in equipment_qs:
            if eq.next_maintenance_date:
                if eq.next_maintenance_date < today:
                    overdue_equipment.append(eq)
                elif eq.next_maintenance_date <= warning_date:
                    upcoming_equipment.append(eq)

        # ========== КЛЮЧЕВЫЕ СРОКИ ==========
        categories_qs = KeyDeadlineCategory.objects.filter(is_active=True).prefetch_related('items')

        # КРИТИЧНО: Применяем фильтрацию по правам ВСЕГДА через AccessControlHelper
        categories_qs = AccessControlHelper.filter_queryset(categories_qs, user, self.request)

        # Дополнительная фильтрация по выбранной организации (если указана)
        if selected_org:
            categories_qs = categories_qs.filter(organization=selected_org)

        overdue_deadlines = []
        upcoming_deadlines = []

        for category in categories_qs:
            for item in category.items.all():
                if item.next_date:
                    if item.next_date < today:
                        overdue_deadlines.append(item)
                    elif item.next_date <= warning_date:
                        upcoming_deadlines.append(item)

        # ========== МЕДИЦИНСКИЕ ОСМОТРЫ ==========
        medical_qs = EmployeeMedicalExamination.objects.select_related('employee', 'harmful_factor')

        # КРИТИЧНО: Фильтрация по employee.organization через AccessControlHelper
        # Поскольку модель EmployeeMedicalExamination не имеет прямого поля organization,
        # фильтруем через связанный Employee
        if not user.is_superuser:
            # Получаем доступных сотрудников
            from directory.models import Employee
            accessible_employees_qs = AccessControlHelper.filter_queryset(
                Employee.objects.all(), user, self.request
            )
            medical_qs = medical_qs.filter(employee__in=accessible_employees_qs)

        # Дополнительная фильтрация по выбранной организации (если указана)
        if selected_org:
            medical_qs = medical_qs.filter(employee__organization=selected_org)

        overdue_medical = []
        upcoming_medical = []

        for exam in medical_qs:
            if exam.next_date:
                if exam.next_date < today:
                    overdue_medical.append(exam)
                elif exam.next_date <= warning_date:
                    upcoming_medical.append(exam)

        # ========== СТАТИСТИКА ==========
        context.update({
            # Оборудование
            'total_equipment': equipment_qs.count(),
            'overdue_equipment': overdue_equipment,
            'overdue_equipment_count': len(overdue_equipment),
            'upcoming_equipment': upcoming_equipment,
            'upcoming_equipment_count': len(upcoming_equipment),

            # Ключевые сроки
            'total_deadlines': sum(c.items.count() for c in categories_qs),
            'overdue_deadlines': overdue_deadlines,
            'overdue_deadlines_count': len(overdue_deadlines),
            'upcoming_deadlines': upcoming_deadlines,
            'upcoming_deadlines_count': len(upcoming_deadlines),

            # Медицинские осмотры
            'total_medical': medical_qs.count(),
            'overdue_medical': overdue_medical,
            'overdue_medical_count': len(overdue_medical),
            'upcoming_medical': upcoming_medical,
            'upcoming_medical_count': len(upcoming_medical),

            # Общее
            'total_overdue': len(overdue_equipment) + len(overdue_deadlines) + len(overdue_medical),
            'total_upcoming': len(upcoming_equipment) + len(upcoming_deadlines) + len(upcoming_medical),
        })

        return context
