# D:\YandexDisk\OT_online\directory\views\home.py

from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import render
from django.http import JsonResponse
from directory.forms.employee import EmployeeForm  # Форма из admin
from directory.models import Employee
import logging

logger = logging.getLogger(__name__)

class HomePageView(LoginRequiredMixin, CreateView):
    """
    🏠 Главная страница (публичная форма), используем EmployeeForm (админскую).
    """
    template_name = 'directory/home.html'
    form_class = EmployeeForm
    success_url = reverse_lazy('directory:home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # фильтрация по организациям
        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            if form.cleaned_data.get('preview'):
                return render(request, 'directory/preview.html', {
                    'form': form,
                    'data': form.cleaned_data
                })
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(
                self.request,
                f"✅ Сотрудник {form.instance.full_name_nominative} успешно создан!"
            )
            logger.info(
                f"User {self.request.user} created employee {form.instance}",
                extra={
                    'user_id': self.request.user.id,
                    'employee_id': form.instance.id
                }
            )
            return response
        except Exception as e:
            logger.error(
                f"Error creating employee: {str(e)}",
                extra={
                    'user_id': self.request.user.id,
                    'form_data': form.cleaned_data
                }
            )
            messages.error(
                self.request,
                f"❌ Ошибка при создании сотрудника: {str(e)}"
            )
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_employees'] = Employee.objects.filter(
            organization__in=self.request.user.profile.organizations.all()
        ).order_by('-id')[:5]
        return context
