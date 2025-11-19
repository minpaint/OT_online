# deadline_control/views/medical.py
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import timedelta

from deadline_control.models.medical_norm import EmployeeMedicalExamination
from directory.models import Employee


class MedicalExaminationListView(LoginRequiredMixin, ListView):
    """
    Список сотрудников с медицинскими осмотрами.

    Отображает сотрудников, у которых есть медосмотры, группирует по статусу.
    Одна строка = один сотрудник с информацией о всех его вредных факторах.
    """
    model = EmployeeMedicalExamination
    template_name = 'deadline_control/medical/list.html'
    context_object_name = 'employees_with_medical'

    def get_queryset(self):
        """
        Получаем сотрудников, должность которых требует прохождения медосмотров.

        Учитывает два источника вредных факторов:
        1. PositionMedicalFactor (переопределения для конкретной должности)
        2. MedicalExaminationNorm (эталонные нормы по названию профессии)
        """
        from directory.models import Employee
        from deadline_control.models import MedicalExaminationNorm
        from django.db.models import Q

        # Находим все уникальные названия профессий из эталонных норм
        position_names_with_norms = MedicalExaminationNorm.objects.values_list(
            'position_name', flat=True
        ).distinct()

        # Находим сотрудников, чья должность требует медосмотров:
        # - Либо у должности есть PositionMedicalFactor
        # - Либо название должности есть в MedicalExaminationNorm
        qs = Employee.objects.exclude(
            status__in=['candidate', 'fired']
        ).filter(
            Q(position__medical_factors__isnull=False) |  # Есть переопределения
            Q(position__position_name__in=position_names_with_norms)  # Есть в эталонах
        ).distinct()

        # Фильтрация по организациям
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)

        # Prefetch для оптимизации запросов
        qs = qs.select_related(
            'organization',
            'position'
        ).prefetch_related(
            'medical_examinations__harmful_factor',
            'position__medical_factors__harmful_factor'  # Префетч для get_medical_status
        )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Разделяем сотрудников на категории на основе get_medical_status()
        no_date = []
        overdue = []
        upcoming = []
        normal = []

        for employee in context['employees_with_medical']:
            medical_status = employee.get_medical_status()

            if not medical_status:
                # Нет медосмотров - пропускаем
                continue

            # Добавляем статус к объекту сотрудника для использования в шаблоне
            employee.medical_status_info = medical_status

            # Распределяем по категориям
            status = medical_status['status']
            if status == 'no_date':
                no_date.append(employee)
            elif status == 'expired':
                overdue.append(employee)
            elif status == 'upcoming':
                upcoming.append(employee)
            else:
                normal.append(employee)

        context['no_date'] = no_date
        context['overdue'] = overdue
        context['upcoming'] = upcoming
        context['normal'] = normal

        return context


@login_required
@require_POST
def update_medical_date(request, pk):
    """Обновление даты следующего медосмотра (ручное редактирование)"""
    exam = get_object_or_404(EmployeeMedicalExamination, pk=pk)

    # Проверка прав доступа
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        allowed_orgs = request.user.profile.organizations.all()
        if exam.employee.organization not in allowed_orgs:
            messages.error(request, 'У вас нет прав для выполнения этой операции')
            return redirect('deadline_control:medical:list')

    date_str = request.POST.get('next_date')
    notes = request.POST.get('notes', '')

    if date_str:
        new_date = parse_date(date_str)
        if new_date:
            exam.next_date = new_date
            if notes:
                exam.notes = notes
            exam.save()
            messages.success(request, f'Дата следующего медосмотра для {exam.employee} обновлена')

    # Если запрос AJAX, возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'next_date': exam.next_date.isoformat() if exam.next_date else None,
            'days_until': exam.days_until_next()
        })

    return redirect('deadline_control:medical:list')


@login_required
@require_POST
def update_employee_medical_examinations(request, employee_id):
    """
    Обновляет ВСЕ медосмотры сотрудника одной датой.

    Применяет указанную дату ко всем медосмотрам сотрудника,
    автоматически рассчитывая следующую дату на основе периодичности каждого вредного фактора.
    """
    from directory.models import Employee

    employee = get_object_or_404(Employee, pk=employee_id)

    # Проверка прав доступа
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        allowed_orgs = request.user.profile.organizations.all()
        if employee.organization not in allowed_orgs:
            messages.error(request, 'У вас нет прав для выполнения этой операции')
            return redirect('deadline_control:medical:list')

    # Получаем дату прохождения медосмотра из формы
    date_str = request.POST.get('examination_date')
    examination_date = parse_date(date_str) if date_str else timezone.now().date()

    # Получаем все медосмотры сотрудника
    examinations = employee.medical_examinations.all()

    # Применяем дату ко всем медосмотрам
    updated_count = 0
    for exam in examinations:
        exam.perform_examination(examination_date)
        updated_count += 1

    # Получаем обновленный статус
    medical_status = employee.get_medical_status()

    messages.success(
        request,
        f'Дата медосмотра ({examination_date.strftime("%d.%m.%Y")}) применена к {updated_count} медосмотрам. '
        f'Следующий медосмотр: {medical_status["next_date"].strftime("%d.%m.%Y")} '
        f'(мин. периодичность: {medical_status["min_periodicity"]} мес.)'
    )

    # Если запрос AJAX, возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'date_completed': medical_status['date_completed'].isoformat() if medical_status['date_completed'] else None,
            'next_date': medical_status['next_date'].isoformat() if medical_status['next_date'] else None,
            'days_until': medical_status['days_until'],
            'min_periodicity': medical_status['min_periodicity'],
            'updated_count': updated_count,
        })

    return redirect('deadline_control:medical:list')


@login_required
@require_POST
def perform_medical_examination(request, pk):
    """
    Проведение медицинского осмотра - аналог perform_maintenance для оборудования.
    Автоматически рассчитывает следующую дату на основе периодичности вредного фактора.
    """
    exam = get_object_or_404(EmployeeMedicalExamination, pk=pk)

    # Проверка прав доступа
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        allowed_orgs = request.user.profile.organizations.all()
        if exam.employee.organization not in allowed_orgs:
            messages.error(request, 'У вас нет прав для выполнения этой операции')
            return redirect('deadline_control:medical:list')

    # Получаем дату прохождения медосмотра из формы (или используем сегодня)
    date_str = request.POST.get('examination_date')
    examination_date = parse_date(date_str) if date_str else None

    # Проводим медосмотр (автоматически рассчитывает следующую дату)
    exam.perform_examination(examination_date)

    messages.success(
        request,
        f'Медосмотр для "{exam.employee.full_name_nominative}" проведен. '
        f'Следующий медосмотр: {exam.next_date.strftime("%d.%m.%Y")} '
        f'(периодичность: {exam.harmful_factor.periodicity} мес.)'
    )

    # Если запрос AJAX, возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'date_completed': exam.date_completed.isoformat() if exam.date_completed else None,
            'next_date': exam.next_date.isoformat() if exam.next_date else None,
            'days_until': exam.days_until_next(),
            'periodicity': exam.harmful_factor.periodicity
        })

    return redirect('deadline_control:medical:list')


@login_required
@require_POST
def update_multiple_medical_examinations(request):
    """
    Массово обновляет медосмотры для нескольких выбранных сотрудников.
    Принимает JSON с 'employee_ids' и 'examination_date'.
    """
    try:
        data = json.loads(request.body)
        employee_ids = data.get('employee_ids', [])
        date_str = data.get('examination_date')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    if not employee_ids or not date_str:
        return JsonResponse({'success': False, 'error': 'Missing employee_ids or examination_date'}, status=400)

    examination_date = parse_date(date_str)
    if not examination_date:
        return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)

    # Получаем queryset сотрудников для обновления
    qs = Employee.objects.filter(id__in=employee_ids)

    # Проверка прав доступа: все выбранные сотрудники должны быть в доступных организациях
    if not request.user.is_superuser and hasattr(request.user, 'profile'):
        allowed_orgs = request.user.profile.organizations.all()
        # Проверяем, что все сотрудники из qs принадлежат к разрешенным организациям
        if qs.exclude(organization__in=allowed_orgs).exists():
            return JsonResponse({'success': False, 'error': 'You do not have permission to update one or more of the selected employees.'}, status=403)

    updated_employee_count = 0
    for employee in qs:
        # Получаем все медосмотры сотрудника (не отключенные)
        examinations_to_update = employee.medical_examinations.filter(is_disabled=False)

        if examinations_to_update.exists():
            updated_employee_count += 1
            for exam in examinations_to_update:
                exam.perform_examination(examination_date)

    if updated_employee_count > 0:
        messages.success(
            request,
            f'Дата медосмотра ({examination_date.strftime("%d.%m.%Y")}) успешно применена к {updated_employee_count} сотрудникам.'
        )

    return JsonResponse({'success': True, 'updated_count': updated_employee_count})


class EmployeeMedicalDetailView(LoginRequiredMixin, DetailView):
    """
    Детальная страница медосмотров конкретного сотрудника.
    Показывает все медосмотры сотрудника с возможностью редактирования.
    """
    model = Employee
    template_name = 'deadline_control/employee_medical_detail.html'
    context_object_name = 'employee'

    def get_queryset(self):
        qs = super().get_queryset()

        # Фильтрация по организациям
        if not self.request.user.is_superuser and hasattr(self.request.user, 'profile'):
            allowed_orgs = self.request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)

        return qs.select_related(
            'organization',
            'position'
        ).prefetch_related(
            'medical_examinations__harmful_factor'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем общий статус медосмотров
        context['medical_status'] = self.object.get_medical_status()

        # Получаем все медосмотры сотрудника
        context['examinations'] = self.object.medical_examinations.all().select_related('harmful_factor')

        return context
