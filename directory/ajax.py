from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from directory.models import StructuralSubdivision, Department, Position, Document, Equipment

@login_required
def get_subdivisions(request):
    """Возвращает структурные подразделения по выбранной организации."""
    organization_id = request.GET.get('organization')
    if not organization_id or organization_id.strip() == '':
        return JsonResponse([], safe=False)
    subdivisions = StructuralSubdivision.objects.filter(
        organization_id=organization_id
    ).values('id', 'name')
    return JsonResponse(list(subdivisions), safe=False)

@login_required
def get_departments(request):
    """Возвращает отделы по выбранной организации и подразделению."""
    organization_id = request.GET.get('organization')
    subdivision_id = request.GET.get('subdivision')
    if (not organization_id or organization_id.strip() == '') or (not subdivision_id or subdivision_id.strip() == ''):
        return JsonResponse([], safe=False)
    departments = Department.objects.filter(
        organization_id=organization_id,
        subdivision_id=subdivision_id
    ).values('id', 'name')
    return JsonResponse(list(departments), safe=False)

@login_required
def get_positions(request):
    """Возвращает должности по выбранной организации, подразделению и (опционально) отделу."""
    organization_id = request.GET.get('organization')
    if not organization_id or organization_id.strip() == '':
        return JsonResponse([], safe=False)
    subdivision_id = request.GET.get('subdivision')
    department_id = request.GET.get('department')
    positions = Position.objects.filter(organization_id=organization_id)
    if subdivision_id and subdivision_id.strip() != '':
        positions = positions.filter(subdivision_id=subdivision_id)
    if department_id and department_id.strip() != '':
        positions = positions.filter(department_id=department_id)
    positions_data = list(positions.values('id', 'position_name'))
    return JsonResponse(positions_data, safe=False)

@login_required
def get_documents(request):
    """Возвращает документы по выбранной организации, подразделению и (опционально) отделу."""
    organization_id = request.GET.get('organization')
    if not organization_id or organization_id.strip() == '':
        return JsonResponse([], safe=False)
    subdivision_id = request.GET.get('subdivision')
    department_id = request.GET.get('department')
    documents = Document.objects.filter(organization_id=organization_id)
    if subdivision_id and subdivision_id.strip() != '':
        documents = documents.filter(subdivision_id=subdivision_id)
    if department_id and department_id.strip() != '':
        documents = documents.filter(department_id=department_id)
    return JsonResponse(list(documents.values('id', 'name')), safe=False)

@login_required
def get_equipment(request):
    """Возвращает оборудование по выбранной организации, подразделению и (опционально) отделу."""
    organization_id = request.GET.get('organization')
    if not organization_id or organization_id.strip() == '':
        return JsonResponse([], safe=False)
    subdivision_id = request.GET.get('subdivision')
    department_id = request.GET.get('department')
    equipment = Equipment.objects.filter(organization_id=organization_id)
    if subdivision_id and subdivision_id.strip() != '':
        equipment = equipment.filter(subdivision_id=subdivision_id)
    if department_id and department_id.strip() != '':
        equipment = equipment.filter(department_id=department_id)
    return JsonResponse(list(equipment.values('id', 'equipment_name')), safe=False)
