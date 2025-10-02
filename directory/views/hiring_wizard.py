from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse

from directory.models import (
    Employee,
    EmployeeHiring,
    Organization,
    Position,
    StructuralSubdivision,
    Department
)
from directory.forms.hiring import CombinedEmployeeHiringForm
from directory.utils.declension import decline_full_name
from directory.models.medical_norm import MedicalExaminationNorm


class SimpleHiringView(LoginRequiredMixin, FormView):
    """
    🧙‍♂️ Упрощенная форма приема на работу вместо многошагового мастера.
    Все поля представлены на одной странице с динамическим отображением
    дополнительных полей для медосмотра и СИЗ.
    """
    template_name = 'directory/hiring/simple_form.html'
    form_class = CombinedEmployeeHiringForm
    success_url = reverse_lazy('directory:hiring:hiring_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Прием на работу: Новый сотрудник')

        # Добавляем список доступных организаций
        if self.request.user and hasattr(self.request.user, 'profile'):
            context['organizations'] = self.request.user.profile.organizations.all()
        else:
            context['organizations'] = Organization.objects.all()

        return context

    @transaction.atomic
    def form_valid(self, form):
        """
        Обработка валидной формы с сохранением сотрудника и записи о приеме.
        """
        try:
            # Получаем данные формы
            data = form.cleaned_data

            # Создаем сотрудника
            employee = Employee(
                full_name_nominative=data['full_name_nominative'],
                date_of_birth=data.get('date_of_birth'),
                place_of_residence=data.get('place_of_residence'),
                organization=data['organization'],
                subdivision=data.get('subdivision'),
                department=data.get('department'),
                position=data['position'],
                height=data.get('height'),
                clothing_size=data.get('clothing_size'),
                shoe_size=data.get('shoe_size'),
                hire_date=timezone.now().date(),
                start_date=timezone.now().date(),
                contract_type=data.get('contract_type', 'standard'),
                status='active'
            )
            employee.save()

            # Создаем запись о приеме
            hiring = EmployeeHiring(
                employee=employee,
                hiring_date=timezone.now().date(),
                start_date=timezone.now().date(),
                hiring_type=data['hiring_type'],
                organization=data['organization'],
                subdivision=data.get('subdivision'),
                department=data.get('department'),
                position=data['position'],
                created_by=self.request.user
            )
            hiring.save()

            # Добавляем сообщение об успехе
            messages.success(
                self.request,
                _('Сотрудник {} успешно принят на работу').format(employee.full_name_nominative)
            )

            # Изменяем URL редиректа на детали записи о приеме
            self.success_url = reverse('directory:hiring:hiring_detail', kwargs={'pk': hiring.pk})

            return super().form_valid(form)

        except Exception as e:
            # Логируем ошибку и добавляем сообщение
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при создании сотрудника: {str(e)}")

            messages.error(
                self.request,
                _('Произошла ошибка при создании сотрудника: {}').format(str(e))
            )

            return self.form_invalid(form)


@login_required
def position_requirements_api(request, position_id):
    """
    🔍 API для получения информации о требованиях должности.

    Проверяет, требуется ли медосмотр и СИЗ для выбранной должности.
    Используется в форме приема на работу для определения необходимых полей.

    Args:
        request: HttpRequest
        position_id: ID должности

    Returns:
        JsonResponse с данными о требованиях должности
    """
    try:
        # Получаем должность или 404
        position = get_object_or_404(Position, pk=position_id)

        # Проверяем переопределения для медосмотра
        has_custom_medical = position.medical_factors.filter(is_disabled=False).exists()

        # Проверяем эталонные нормы, если нет переопределений
        has_reference_medical = False
        if not has_custom_medical:
            has_reference_medical = MedicalExaminationNorm.objects.filter(
                position_name=position.position_name
            ).exists()

        # Проверяем переопределения для СИЗ
        has_custom_siz = position.siz_norms.exists()

        # Проверяем эталонные нормы СИЗ, если нет переопределений
        has_reference_siz = False
        if not has_custom_siz:
            has_reference_siz = Position.find_reference_norms(position.position_name).exists()

        # Формируем ответ
        response_data = {
            'position_id': position.id,
            'position_name': position.position_name,
            'needs_medical': has_custom_medical or has_reference_medical,
            'needs_siz': has_custom_siz or has_reference_siz,
            'status': 'success'
        }

        return JsonResponse(response_data)

    except Exception as e:
        # Логируем ошибку
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка в position_requirements_api для должности ID={position_id}: {str(e)}")

        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)