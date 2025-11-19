# deadline_control/views/dashboard.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from deadline_control.models import Equipment, KeyDeadlineCategory, KeyDeadlineItem
from deadline_control.models.medical_norm import EmployeeMedicalExamination


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Главная страница приложения Контроль сроков с обзором всех истекающих сроков
    """
    template_name = 'deadline_control/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Фильтрация по организациям пользователя
        user = self.request.user
        if not user.is_superuser and hasattr(user, 'profile'):
            allowed_orgs = user.profile.organizations.all()
        else:
            allowed_orgs = None

        # Фильтр по конкретной организации из GET-параметра
        org_id = self.request.GET.get('org')
        selected_org = None
        if org_id:
            from directory.models import Organization
            try:
                selected_org = Organization.objects.get(pk=org_id)
                # Проверяем права доступа
                if allowed_orgs and selected_org not in allowed_orgs:
                    selected_org = None
                context['selected_org'] = selected_org
            except Organization.DoesNotExist:
                pass

        today = timezone.now().date()
        warning_date = today + timedelta(days=14)

        # ========== ОБОРУДОВАНИЕ ==========
        equipment_qs = Equipment.objects.select_related('organization', 'subdivision', 'department')
        if selected_org:
            equipment_qs = equipment_qs.filter(organization=selected_org)
        elif allowed_orgs:
            equipment_qs = equipment_qs.filter(organization__in=allowed_orgs)

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
        if selected_org:
            categories_qs = categories_qs.filter(organization=selected_org)
        elif allowed_orgs:
            categories_qs = categories_qs.filter(organization__in=allowed_orgs)

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
        if selected_org:
            medical_qs = medical_qs.filter(employee__organization=selected_org)
        elif allowed_orgs:
            medical_qs = medical_qs.filter(employee__organization__in=allowed_orgs)

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
