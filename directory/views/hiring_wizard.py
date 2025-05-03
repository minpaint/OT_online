# directory/views/hiring_wizard.py
"""
👨‍💼 Представления для многошаговой формы приема на работу
Использует FormWizard для реализации шагов
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone  # Исправленный импорт timezone

# Добавляем импорт формтулс
from formtools.wizard.views import SessionWizardView

# Импортируем ваши классы форм
from directory.forms.hiring_wizard import Step1BasicInfoForm, Step2MedicalInfoForm, Step3SIZInfoForm

# Прямые импорты для моделей чтобы избежать проблем инициализации
from directory.models.employee import Employee
from directory.models.hiring import EmployeeHiring
from directory.models.position import Position
from directory.models.medical_norm import MedicalExaminationNorm
from directory.utils.declension import decline_full_name

class HiringWizardView(LoginRequiredMixin, SessionWizardView):
    """Мастер формы для пошагового приема на работу"""
    template_name = 'directory/hiring/wizard_form.html'
    form_list = [
        ('basic_info', Step1BasicInfoForm),
        ('medical_info', Step2MedicalInfoForm),
        ('siz_info', Step3SIZInfoForm)
    ]

    def get_form_kwargs(self, step=None):
        """Передаем пользователя в форму"""
        kwargs = super().get_form_kwargs(step)
        if step == 'basic_info':
            kwargs['user'] = self.request.user
        return kwargs

    def get_form_initial(self, step):
        """Подготавливаем начальные данные для каждого шага"""
        initial = super().get_form_initial(step)

        # Для шага 1 - базовые значения по умолчанию
        if step == 'basic_info':
            initial['hiring_type'] = 'new'

        return initial

    def get_context_data(self, form, **kwargs):
        """Добавляем контекст для шаблона"""
        context = super().get_context_data(form, **kwargs)

        # Общие данные для всех шагов
        current_step = self.steps.current
        context['title'] = _('Прием на работу: Шаг {0}').format(
            list(self.get_form_list()).index(current_step) + 1
        )

        # Для третьего шага показываем информацию о нормах СИЗ
        if current_step == 'siz_info':
            basic_data = self.get_cleaned_data_for_step('basic_info')
            if basic_data and 'position' in basic_data:
                position = basic_data['position']
                context['siz_norms'] = self._get_siz_norms(position)

        return context

    def process_step(self, form):
        """Обработка каждого шага"""
        step_data = super().process_step(form)
        step = self.steps.current

        # Для шага basic_info проверяем необходимость медосмотра и СИЗ
        if step == 'basic_info':
            position = form.cleaned_data.get('position')

            # Сохраняем флаги в хранилище
            self.storage.extra_data['needs_medical'] = self._position_needs_medical(position)
            self.storage.extra_data['needs_siz'] = self._position_needs_siz(position)

        return step_data

    def get_form_step_files(self, form):
        """Сохранение файлов из формы (если будут нужны)"""
        return super().get_form_step_files(form)

    def get_next_step(self, step=None):
        """Определяем следующий шаг в зависимости от логических условий"""
        if step is None:
            step = self.steps.current

        next_step = super().get_next_step(step)

        # Если текущий шаг - basic_info, определяем, нужны ли доп. шаги
        if step == 'basic_info':
            # Получаем данные из формы
            cleaned_data = self.get_cleaned_data_for_step(step)
            if cleaned_data:
                position = cleaned_data.get('position')

                # Проверяем, требуется ли медосмотр для этой должности
                self.storage.extra_data['needs_medical'] = self._position_needs_medical(position)
                self.storage.extra_data['needs_siz'] = self._position_needs_siz(position)

                needs_medical = self.storage.extra_data.get('needs_medical', False)
                needs_siz = self.storage.extra_data.get('needs_siz', False)

                if not needs_medical:
                    # Пропускаем шаг medical_info
                    if next_step == 'medical_info':
                        # Если нужен шаг СИЗ, идем к нему
                        if needs_siz:
                            return 'siz_info'
                        # Иначе переходим к завершению
                        return None

        # Если текущий шаг - medical_info, проверяем, нужен ли шаг СИЗ
        elif step == 'medical_info':
            needs_siz = self.storage.extra_data.get('needs_siz', False)
            if not needs_siz:
                # Пропускаем шаг siz_info
                return None

        return next_step

    def done(self, form_list, **kwargs):
        """Сохранение результатов всех форм"""
        # Получаем данные со всех шагов
        all_data = {}
        for form in form_list:
            all_data.update(form.cleaned_data)

        # Создаем сотрудника и запись о приеме в транзакции
        try:
            with transaction.atomic():
                # Подготавливаем данные для модели Employee
                employee_data = {
                    'full_name_nominative': all_data['full_name_nominative'],
                    'full_name_dative': decline_full_name(all_data['full_name_nominative'], 'datv'),
                    'organization': all_data['organization'],
                    'subdivision': all_data.get('subdivision'),
                    'department': all_data.get('department'),
                    'position': all_data['position'],
                    'status': 'active',
                    'hire_date': timezone.now().date(),
                    'start_date': timezone.now().date(),
                    'contract_type': 'standard',
                }

                # Добавляем данные из шага медосмотра, если он был
                if 'date_of_birth' in all_data:
                    employee_data['date_of_birth'] = all_data['date_of_birth']
                    employee_data['place_of_residence'] = all_data['place_of_residence']

                # Добавляем данные из шага СИЗ, если он был
                if 'height' in all_data:
                    employee_data['height'] = all_data['height']
                    employee_data['clothing_size'] = all_data['clothing_size']
                    employee_data['shoe_size'] = all_data['shoe_size']

                # Создаем сотрудника
                employee = Employee.objects.create(**employee_data)

                # Создаем запись о приеме
                hiring = EmployeeHiring.objects.create(
                    employee=employee,
                    hiring_date=timezone.now().date(),
                    start_date=timezone.now().date(),
                    hiring_type=all_data['hiring_type'],
                    organization=all_data['organization'],
                    subdivision=all_data.get('subdivision'),
                    department=all_data.get('department'),
                    position=all_data['position'],
                    created_by=self.request.user,
                )

                messages.success(
                    self.request,
                    _('Сотрудник {0} успешно принят на работу').format(employee.full_name_nominative)
                )

                # Перенаправляем на страницу созданной записи о приеме
                return redirect('directory:hiring:hiring_detail', pk=hiring.pk)

        except Exception as e:
            messages.error(
                self.request,
                _('Ошибка при создании записи о приеме: {0}').format(str(e))
            )
            # Возвращаемся на первый шаг
            return redirect('directory:hiring:hiring_wizard')

    def _position_needs_medical(self, position):
        """Проверяет, нужен ли медосмотр для данной должности"""
        if not position:
            return False

        # Проверяем переопределения для конкретной должности
        has_custom_medical = position.medical_factors.filter(is_disabled=False).exists()

        # Проверяем эталонные нормы, если нет переопределений
        if not has_custom_medical:
            has_reference_medical = MedicalExaminationNorm.objects.filter(
                position_name=position.position_name
            ).exists()
            return has_reference_medical

        return has_custom_medical

    def _position_needs_siz(self, position):
        """Проверяет, нужны ли СИЗ для данной должности"""
        if not position:
            return False

        # Проверяем переопределения для конкретной должности
        has_custom_siz = position.siz_norms.exists()

        # Проверяем эталонные нормы, если нет переопределений
        if not has_custom_siz:
            has_reference_siz = Position.find_reference_norms(position.position_name).exists()
            return has_reference_siz

        return has_custom_siz

    def _get_siz_norms(self, position):
        """Получает нормы СИЗ для отображения"""
        if not position:
            return []

        # Проверяем переопределения для конкретной должности
        custom_norms = position.siz_norms.select_related('siz').all()
        if custom_norms.exists():
            return custom_norms

        # Проверяем эталонные нормы
        reference_norms = Position.find_reference_norms(position.position_name)
        return reference_norms