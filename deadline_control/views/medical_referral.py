"""
Views для системы выдачи направлений на медицинский осмотр.
"""
import json
import os
from datetime import datetime
from django.http import JsonResponse, FileResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib import messages

from directory.models import Employee
from directory.utils.permissions import AccessControlHelper
from deadline_control.models import (
    MedicalReferral,
    PositionMedicalFactor,
    MedicalExaminationNorm,
    HarmfulFactor,
    MedicalSettings
)

try:
    from docxtpl import DocxTemplate
    DOCXTPL_AVAILABLE = True
except ImportError:
    DOCXTPL_AVAILABLE = False


def get_harmful_factors_for_employee(employee):
    """
    Получает вредные факторы для сотрудника с учётом переопределений.

    Приоритет:
    1. Переопределённые факторы для должности в организации (PositionMedicalFactor)
    2. Эталонные факторы по названию должности (MedicalExaminationNorm)
    """
    position = employee.position

    # 1. Проверяем переопределения для конкретной должности
    overridden_factors = PositionMedicalFactor.objects.filter(
        position=position,
        is_disabled=False  # Только активные факторы
    ).select_related('harmful_factor')

    if overridden_factors.exists():
        # Используем переопределённые факторы
        return [pf.harmful_factor for pf in overridden_factors]

    # 2. Если переопределений нет - берём эталонные нормы по названию должности
    reference_norms = MedicalExaminationNorm.objects.filter(
        position_name=position.position_name
    ).select_related('harmful_factor')

    return [norm.harmful_factor for norm in reference_norms]


def generate_referral_document(referral):
    """
    Генерирует DOCX документ направления на медосмотр.
    Возвращает путь к сгенерированному файлу.
    """
    if not DOCXTPL_AVAILABLE:
        return None

    # Получаем путь к шаблону из настроек организации или используем эталонный
    medical_settings = MedicalSettings.get_settings(employee.organization)

    if medical_settings and medical_settings.referral_template:
        # Используем шаблон из настроек
        template_path = medical_settings.referral_template.path
    else:
        # Используем эталонный шаблон (исправленная версия)
        template_path = os.path.join(
            settings.MEDIA_ROOT,
            'document_templates',
            'etalon',
            'napravlenie_blank_fixed.docx'
        )
        # Если исправленный шаблон не найден, пробуем оригинальный
        if not os.path.exists(template_path):
            template_path = os.path.join(
                settings.MEDIA_ROOT,
                'document_templates',
                'etalon',
                'napravlenie_blank.docx'
            )

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Шаблон направления не найден: {template_path}")

    # Загружаем шаблон
    doc = DocxTemplate(template_path)

    # Подготавливаем данные для заполнения
    employee = referral.employee
    organization = employee.organization

    # Разбиваем ФИО на части
    name_parts = employee.full_name_nominative.split()
    last_name = name_parts[0] if len(name_parts) > 0 else ''
    first_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

    # Формируем список вредных факторов (только полное наименование)
    factors_list = []
    for factor in referral.harmful_factors.all():
        factors_list.append(factor.full_name)
    harmful_factors_text = '\n'.join(factors_list) if factors_list else 'Не определены'

    # Контекст для шаблона
    context = {
        'organization_name': organization.full_name_ru,
        'organization_name_by': getattr(organization, 'full_name_by', organization.full_name_ru),
        'requisites_ru': getattr(organization, 'requisites_ru', ''),
        'requisites_by': getattr(organization, 'requisites_by', ''),
        'last_name': last_name,
        'first_name': first_name,
        'full_name': employee.full_name_nominative,
        'date_of_birth': referral.employee_birth_date.strftime('%d.%m.%Y'),
        'address': referral.employee_address,
        'position_name': employee.position.position_name,
        'harmful_factors': harmful_factors_text,
        'issue_date': referral.issue_date.strftime('%d.%m.%Y'),
    }

    # Заполняем шаблон
    doc.render(context)

    # Создаём директорию для сохранения
    save_dir = os.path.join(
        settings.MEDIA_ROOT,
        'medical_referrals',
        str(timezone.now().year),
        str(timezone.now().month).zfill(2)
    )
    os.makedirs(save_dir, exist_ok=True)

    # Имя файла
    filename = f"referral_{referral.id}_{employee.full_name_nominative.replace(' ', '_')}.docx"
    filepath = os.path.join(save_dir, filename)

    # Сохраняем документ
    doc.save(filepath)

    # Сохраняем путь в модели (относительный путь от MEDIA_ROOT)
    relative_path = os.path.relpath(filepath, settings.MEDIA_ROOT)
    referral.document.name = relative_path
    referral.save()

    return filepath


class EmployeeReferralDataView(LoginRequiredMixin, View):
    """
    API endpoint для получения данных сотрудника для формы направления.
    GET /deadline-control/medical/referral/employee/{id}/
    """

    def get(self, request, employee_id):
        # Получаем сотрудника
        employee = get_object_or_404(Employee, pk=employee_id)

        # Проверяем права доступа через AccessControlHelper (поддерживает иерархию)
        if not AccessControlHelper.can_access_object(request.user, employee):
            raise PermissionDenied("У вас нет доступа к данному сотруднику")

        # Получаем вредные факторы с учётом приоритета переопределений
        harmful_factors = get_harmful_factors_for_employee(employee)

        # Формируем ответ
        data = {
            'id': employee.id,
            'full_name': employee.full_name_nominative,
            'position': employee.position.position_name,
            'organization': employee.organization.short_name_ru,
            'birth_date': employee.date_of_birth.strftime('%Y-%m-%d') if employee.date_of_birth else '',
            'address': employee.place_of_residence or '',
            'harmful_factors': [
                {
                    'id': factor.id,
                    'short_name': factor.short_name,
                    'full_name': factor.full_name
                }
                for factor in harmful_factors
            ]
        }

        return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
class GenerateReferralView(LoginRequiredMixin, View):
    """
    API endpoint для генерации направления на медосмотр.
    POST /deadline-control/medical/referral/generate/
    """

    def post(self, request):
        try:
            # Парсим JSON данные
            data = json.loads(request.body)
            employee_id = data.get('employee_id')
            full_name = data.get('full_name', '').strip()
            birth_date_str = data.get('birth_date')
            address = data.get('address', '').strip()

            if not employee_id or not full_name or not birth_date_str or not address:
                return JsonResponse({
                    'success': False,
                    'error': 'Не все обязательные поля заполнены'
                }, status=400)

            # Получаем сотрудника
            employee = get_object_or_404(Employee, pk=employee_id)

            # Проверяем права доступа через AccessControlHelper (поддерживает иерархию)
            if not AccessControlHelper.can_access_object(request.user, employee):
                raise PermissionDenied("У вас нет доступа к данному сотруднику")

            # Парсим дату рождения
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()

            # Обновляем данные сотрудника, если они изменились
            updated = False
            if employee.full_name_nominative != full_name:
                employee.full_name_nominative = full_name
                updated = True
            if employee.date_of_birth != birth_date:
                employee.date_of_birth = birth_date
                updated = True
            if employee.place_of_residence != address:
                employee.place_of_residence = address
                updated = True
            if updated:
                employee.save()

            # Получаем вредные факторы
            harmful_factors = get_harmful_factors_for_employee(employee)

            # Создаём запись направления
            referral = MedicalReferral.objects.create(
                employee=employee,
                employee_birth_date=birth_date,
                employee_address=address,
                issued_by=request.user
            )

            # Добавляем вредные факторы
            referral.harmful_factors.set(harmful_factors)

            # Генерируем DOCX документ
            document_url = None
            if DOCXTPL_AVAILABLE:
                filepath = generate_referral_document(referral)
                if filepath and referral.document:
                    document_url = referral.document.url

            return JsonResponse({
                'success': True,
                'referral_id': referral.id,
                'message': 'Направление успешно создано',
                'document_url': document_url
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат данных'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class ExistingEmployeeReferralView(LoginRequiredMixin, View):
    """
    Форма для выдачи направления на медосмотр существующему сотруднику.
    """

    def get(self, request, employee_id):
        from django.shortcuts import render, get_object_or_404
        from directory.models import Employee

        # Получаем сотрудника
        employee = get_object_or_404(Employee, pk=employee_id)

        # Проверяем права доступа через AccessControlHelper (поддерживает иерархию)
        if not AccessControlHelper.can_access_object(request.user, employee):
            messages.error(request, 'У вас нет доступа к этому сотруднику')
            return redirect('deadline_control:medical:list')

        # Получаем вредные факторы для сотрудника
        harmful_factors = get_harmful_factors_for_employee(employee)

        context = {
            'employee': employee,
            'harmful_factors': harmful_factors,
        }
        return render(request, 'deadline_control/existing_employee_referral.html', context)


class NewEmployeeReferralView(LoginRequiredMixin, View):
    """
    Форма для выдачи направления на медосмотр новому сотруднику (до приёма на работу).
    GET: Показать форму
    POST: Генерировать направление
    """

    def get(self, request):
        from django.shortcuts import render
        from directory.models import Position, Organization

        # Получаем организации пользователя
        if request.user.is_superuser:
            organizations = Organization.objects.all()
        else:
            # Проверяем наличие profile
            if hasattr(request.user, 'profile'):
                organizations = request.user.profile.organizations.all()
            else:
                organizations = Organization.objects.none()

        # Автовыбор организации, если она одна
        selected_organization_id = None
        if organizations.count() == 1:
            selected_organization_id = organizations.first().id

        # Получаем уникальные названия профессий
        position_names = Position.objects.values_list(
            'position_name', flat=True
        ).distinct().order_by('position_name')

        context = {
            'organizations': organizations,
            'position_names': list(position_names),
            'selected_organization_id': selected_organization_id,
        }
        return render(request, 'deadline_control/new_employee_referral.html', context)

    def post(self, request):
        from django.shortcuts import render
        from directory.models import Position, Organization

        # Получаем данные из формы
        full_name = request.POST.get('full_name', '').strip()
        birth_date_str = request.POST.get('birth_date', '')
        address = request.POST.get('address', '').strip()
        position_name = request.POST.get('position_name', '')
        organization_id = request.POST.get('organization_id', '')

        errors = []

        # Валидация
        if not full_name:
            errors.append('ФИО обязательно для заполнения')
        if not birth_date_str:
            errors.append('Дата рождения обязательна')
        if not address:
            errors.append('Адрес обязателен')
        if not position_name:
            errors.append('Профессия обязательна')
        if not organization_id:
            errors.append('Организация обязательна')

        # Получаем организации пользователя для формы
        if request.user.is_superuser:
            organizations = Organization.objects.all()
        else:
            # Проверяем наличие profile
            if hasattr(request.user, 'profile'):
                organizations = request.user.profile.organizations.all()
            else:
                organizations = Organization.objects.none()

        position_names = Position.objects.values_list(
            'position_name', flat=True
        ).distinct().order_by('position_name')

        if errors:
            context = {
                'organizations': organizations,
                'position_names': list(position_names),
                'errors': errors,
                'form_data': {
                    'full_name': full_name,
                    'birth_date': birth_date_str,
                    'address': address,
                    'position_name': position_name,
                    'organization_id': organization_id,
                }
            }
            return render(request, 'deadline_control/new_employee_referral.html', context)

        try:
            # Парсим дату
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()

            # Получаем организацию
            organization = Organization.objects.get(pk=organization_id)

            # Проверяем права доступа через AccessControlHelper
            if not AccessControlHelper.can_access_object(request.user, organization):
                raise PermissionDenied("У вас нет доступа к этой организации")

            # Получаем вредные факторы по названию профессии
            harmful_factors = []
            reference_norms = MedicalExaminationNorm.objects.filter(
                position_name=position_name
            ).select_related('harmful_factor')

            for norm in reference_norms:
                harmful_factors.append(norm.harmful_factor)

            if not harmful_factors:
                errors.append(f'Для профессии "{position_name}" не найдены вредные факторы')
                context = {
                    'organizations': organizations,
                    'position_names': list(position_names),
                    'errors': errors,
                    'form_data': {
                        'full_name': full_name,
                        'birth_date': birth_date_str,
                        'address': address,
                        'position_name': position_name,
                        'organization_id': organization_id,
                    }
                }
                return render(request, 'deadline_control/new_employee_referral.html', context)

            # Создаём направление (без привязки к сотруднику - employee=None)
            # Но модель требует employee, поэтому создадим специальную запись
            # Альтернативно - генерируем документ без сохранения в БД

            # Генерируем DOCX документ напрямую
            if not DOCXTPL_AVAILABLE:
                errors.append('Библиотека docxtpl не установлена')
                context = {
                    'organizations': organizations,
                    'position_names': list(position_names),
                    'errors': errors,
                }
                return render(request, 'deadline_control/new_employee_referral.html', context)

            # Получаем шаблон для организации
            medical_settings = MedicalSettings.get_settings(organization)

            if medical_settings and medical_settings.referral_template:
                template_path = medical_settings.referral_template.path
            else:
                template_path = os.path.join(
                    settings.MEDIA_ROOT,
                    'document_templates',
                    'etalon',
                    'napravlenie_blank_fixed.docx'
                )
                if not os.path.exists(template_path):
                    template_path = os.path.join(
                        settings.MEDIA_ROOT,
                        'document_templates',
                        'etalon',
                        'napravlenie_blank.docx'
                    )

            if not os.path.exists(template_path):
                errors.append(f'Шаблон направления не найден')
                context = {
                    'organizations': organizations,
                    'position_names': list(position_names),
                    'errors': errors,
                }
                return render(request, 'deadline_control/new_employee_referral.html', context)

            # Загружаем шаблон
            doc = DocxTemplate(template_path)

            # Разбиваем ФИО на части
            name_parts = full_name.split()
            last_name = name_parts[0] if len(name_parts) > 0 else ''
            first_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            # Формируем список вредных факторов
            factors_list = [factor.full_name for factor in harmful_factors]
            harmful_factors_text = '\n'.join(factors_list) if factors_list else 'Не определены'

            # Контекст для шаблона
            context_doc = {
                'organization_name': organization.full_name_ru,
                'organization_name_by': getattr(organization, 'full_name_by', organization.full_name_ru),
                'requisites_ru': getattr(organization, 'requisites_ru', ''),
                'requisites_by': getattr(organization, 'requisites_by', ''),
                'last_name': last_name,
                'first_name': first_name,
                'full_name': full_name,
                'date_of_birth': birth_date.strftime('%d.%m.%Y'),
                'address': address,
                'position_name': position_name,
                'harmful_factors': harmful_factors_text,
                'issue_date': timezone.now().date().strftime('%d.%m.%Y'),
            }

            # Заполняем шаблон
            doc.render(context_doc)

            # Создаём директорию для сохранения
            save_dir = os.path.join(
                settings.MEDIA_ROOT,
                'medical_referrals',
                'new_employees',
                str(timezone.now().year),
                str(timezone.now().month).zfill(2)
            )
            os.makedirs(save_dir, exist_ok=True)

            # Имя файла
            safe_name = full_name.replace(' ', '_').replace('"', '').replace("'", '')
            filename = f"Направление_на_МО_{safe_name}.docx"
            filepath = os.path.join(save_dir, filename)

            # Сохраняем документ
            doc.save(filepath)

            # Возвращаем файл на скачивание
            from urllib.parse import quote
            response = FileResponse(
                open(filepath, 'rb'),
                as_attachment=True,
                filename=filename,
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            # Для корректной работы с русскими именами файлов
            encoded_filename = quote(filename)
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
            return response

        except Organization.DoesNotExist:
            errors.append('Организация не найдена')
        except Exception as e:
            import traceback
            errors.append(f'Ошибка: {str(e)}')
            # Логируем полную трассировку для отладки
            print(f"Error in NewEmployeeReferralView: {traceback.format_exc()}")

        context = {
            'organizations': organizations,
            'position_names': list(position_names),
            'errors': errors,
            'form_data': {
                'full_name': full_name,
                'birth_date': birth_date_str,
                'address': address,
                'position_name': position_name,
                'organization_id': organization_id,
            }
        }
        return render(request, 'deadline_control/new_employee_referral.html', context)
