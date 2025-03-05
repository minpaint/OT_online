# 📁 directory/views/__init__.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages

from directory.forms import EmployeeHiringForm
from .auth import UserRegistrationView

# Импортируем представления для сотрудников
from .employees import (
    EmployeeListView,
    EmployeeCreateView,
    EmployeeUpdateView,
    EmployeeDeleteView,
    get_subdivisions
)

# Импортируем представления для должностей
from .positions import (
    PositionListView,
    PositionCreateView,
    PositionUpdateView,
    PositionDeleteView,
    get_positions,
    get_departments
)

# 🆕 Импортируем представления для выдачи СИЗ
from .siz_issued import (
    SIZIssueFormView,
    SIZPersonalCardView,
    SIZIssueReturnView,
    employee_siz_issued_list,
)

class HomePageView(LoginRequiredMixin, TemplateView):
    """🏠 Главная страница"""
    template_name = 'directory/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '🏠 Главная'
        context['form'] = EmployeeHiringForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        form = EmployeeHiringForm(request.POST, user=request.user)
        if form.is_valid():
            if form.cleaned_data.get('preview'):
                return render(request, 'directory/preview.html', {
                    'form': form,
                    'data': form.cleaned_data
                })
            employee = form.save()
            messages.success(
                request,
                f"✅ Сотрудник {employee.full_name_nominative} успешно принят на работу"
            )
            return redirect('directory:employees:employee_list')
        return render(request, self.template_name, {
            'form': form,
            'title': '🏠 Главная'
        })

# Экспортируем все представления
__all__ = [
    'HomePageView',
    'EmployeeListView',
    'EmployeeCreateView',
    'EmployeeUpdateView',
    'EmployeeDeleteView',
    'PositionListView',
    'PositionCreateView',
    'PositionUpdateView',
    'PositionDeleteView',
    'get_subdivisions',
    'get_positions',
    'get_departments',
    'UserRegistrationView',
    # 🆕 Добавляем в список экспорта
    'SIZIssueFormView',
    'SIZPersonalCardView',
    'SIZIssueReturnView',
    'employee_siz_issued_list',
]