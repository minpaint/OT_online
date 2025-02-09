# 📁 directory/ajax.py

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.core.cache import cache
from django.core.exceptions import ValidationError

from directory.models import (
    StructuralSubdivision,
    Department,
    Position,
    Document,
    Equipment
)


def validate_organization(organization_id):
    """
    🔍 Проверяет корректность ID организации

    Args:
        organization_id: ID организации
    Raises:
        ValidationError: Если ID пустой или некорректный
    """
    if not organization_id or organization_id.strip() == '':
        raise ValidationError('Не указан ID организации')


@login_required
@require_GET
def get_subdivisions(request):
    """
    📋 Возвращает структурные подразделения по выбранной организации

    Args:
        request: HTTP запрос с параметром organization
    Returns:
        JsonResponse со списком подразделений
    """
    try:
        organization_id = request.GET.get('organization')
        validate_organization(organization_id)

        # 💾 Пробуем получить данные из кэша
        cache_key = f'subdivisions_org_{organization_id}'
        subdivisions = cache.get(cache_key)

        if subdivisions is None:
            subdivisions = list(
                StructuralSubdivision.objects
                .filter(organization_id=organization_id)
                .values('id', 'name')
            )
            # 📦 Кэшируем на 5 минут
            cache.set(cache_key, subdivisions, 300)

        return JsonResponse(subdivisions, safe=False)

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


@login_required
@require_GET
def get_departments(request):
    """
    📋 Возвращает отделы по выбранной организации и подразделению

    Args:
        request: HTTP запрос с параметрами organization и subdivision
    Returns:
        JsonResponse со списком отделов
    """
    try:
        organization_id = request.GET.get('organization')
        subdivision_id = request.GET.get('subdivision')

        validate_organization(organization_id)
        if not subdivision_id or subdivision_id.strip() == '':
            raise ValidationError('Не указан ID подразделения')

        cache_key = f'departments_org_{organization_id}_sub_{subdivision_id}'
        departments = cache.get(cache_key)

        if departments is None:
            departments = list(
                Department.objects
                .filter(
                    organization_id=organization_id,
                    subdivision_id=subdivision_id
                )
                .values('id', 'name')
            )
            cache.set(cache_key, departments, 300)

        return JsonResponse(departments, safe=False)

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


@login_required
@require_GET
def get_positions(request):
    """
    📋 Возвращает должности по выбранной организации, подразделению и отделу

    Args:
        request: HTTP запрос с параметрами organization, subdivision и department
    Returns:
        JsonResponse со списком должностей
    """
    try:
        organization_id = request.GET.get('organization')
        validate_organization(organization_id)

        subdivision_id = request.GET.get('subdivision')
        department_id = request.GET.get('department')

        # 🔍 Формируем базовый запрос
        positions = Position.objects.filter(organization_id=organization_id)

        # 🔄 Добавляем дополнительные фильтры
        if subdivision_id and subdivision_id.strip():
            positions = positions.filter(subdivision_id=subdivision_id)
        if department_id and department_id.strip():
            positions = positions.filter(department_id=department_id)

        positions_data = list(positions.values('id', 'position_name'))
        return JsonResponse(positions_data, safe=False)

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


@login_required
@require_GET
def get_documents(request):
    """
    📋 Возвращает документы по выбранной организации, подразделению и отделу

    Args:
        request: HTTP запрос с параметрами organization, subdivision и department
    Returns:
        JsonResponse со списком документов
    """
    try:
        organization_id = request.GET.get('organization')
        validate_organization(organization_id)

        subdivision_id = request.GET.get('subdivision')
        department_id = request.GET.get('department')

        # 🔍 Формируем базовый запрос
        documents = Document.objects.filter(organization_id=organization_id)

        # 🔄 Добавляем дополнительные фильтры
        if subdivision_id and subdivision_id.strip():
            documents = documents.filter(subdivision_id=subdivision_id)
        if department_id and department_id.strip():
            documents = documents.filter(department_id=department_id)

        documents_data = list(documents.values('id', 'name'))
        return JsonResponse(documents_data, safe=False)

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)


@login_required
@require_GET
def get_equipment(request):
    """
    📋 Возвращает оборудование по выбранной организации, подразделению и отделу

    Args:
        request: HTTP запрос с параметрами organization, subdivision и department
    Returns:
        JsonResponse со списком оборудования
    """
    try:
        organization_id = request.GET.get('organization')
        validate_organization(organization_id)

        subdivision_id = request.GET.get('subdivision')
        department_id = request.GET.get('department')

        # 🔍 Формируем базовый запрос
        equipment = Equipment.objects.filter(organization_id=organization_id)

        # 🔄 Добавляем дополнительные фильтры
        if subdivision_id and subdivision_id.strip():
            equipment = equipment.filter(subdivision_id=subdivision_id)
        if department_id and department_id.strip():
            equipment = equipment.filter(department_id=department_id)

        equipment_data = list(equipment.values('id', 'equipment_name'))
        return JsonResponse(equipment_data, safe=False)

    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)