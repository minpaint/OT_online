from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages

from directory.forms import EmployeeHiringForm
from .auth import UserRegistrationView

# Импорт представлений для сотрудников
from .employees import (
    EmployeeListView,
    EmployeeCreateView,
    EmployeeUpdateView,
    EmployeeDeleteView,
    get_subdivisions
)

# Импорт представлений для должностей
from .positions import (
    PositionListView,
    PositionCreateView,
    PositionUpdateView,
    PositionDeleteView,
    get_positions,
    get_departments
)

class EmployeeHiringView(LoginRequiredMixin, TemplateView):
    """🏠 Главная страница – форма приема на работу"""
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

__all__ = [
    'EmployeeHiringView',  # теперь экспортируем EmployeeHiringView
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
]
