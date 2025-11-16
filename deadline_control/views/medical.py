# deadline_control/views/medical.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.utils import timezone
from datetime import timedelta

from directory.models import EmployeeMedicalExamination


class MedicalExaminationListView(LoginRequiredMixin, ListView):
    """Список медицинских осмотров с контролем сроков"""
    model = EmployeeMedicalExamination
    template_name = 'deadline_control/medical/list.html'
    context_object_name = 'examinations'

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(employee__organization__in=allowed_orgs)
        return qs.select_related('employee', 'employee__organization', 'harmful_factor').order_by('next_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        warning_date = today + timedelta(days=14)

        # Разделяем на категории
        overdue = []
        upcoming = []
        normal = []

        for exam in context['examinations']:
            if exam.next_date:
                if exam.next_date < today:
                    overdue.append(exam)
                elif exam.next_date <= warning_date:
                    upcoming.append(exam)
                else:
                    normal.append(exam)
            else:
                normal.append(exam)

        context['overdue'] = overdue
        context['upcoming'] = upcoming
        context['normal'] = normal

        return context
