# D:\YandexDisk\OT_online\directory\views\home.py

from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import render
from directory.forms.employee_hiring import EmployeeHiringForm  # Подключаем форму найма
from directory.models import Employee
import logging

logger = logging.getLogger(__name__)

class HomePageView(LoginRequiredMixin, CreateView):
    """
    🏠 Главная страница (публичная форма), используем EmployeeHiringForm.
    """
    template_name = 'directory/home.html'
    form_class = EmployeeHiringForm  # Используем обновлённую форму
    success_url = reverse_lazy('directory:home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Фильтрация по организациям
        return kwargs

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(
                self.request,
                f"✅ Сотрудник {form.instance.full_name_nominative} успешно создан!"
            )
            return response
        except Exception as e:
            logger.error(f"Ошибка создания сотрудника: {str(e)}")
            messages.error(
                self.request,
                f"❌ Ошибка при создании сотрудника: {str(e)}"
            )
            return self.form_invalid(form)
