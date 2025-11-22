from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from directory.models import Employee
from directory.utils.permissions import AccessControlHelper


@login_required
def debug_permissions_view(request):
    """
    Отладочная страница для проверки прав доступа
    """
    user = request.user

    # Получаем профиль
    if hasattr(user, 'profile'):
        profile = user.profile
        organizations = profile.organizations.all()
        subdivisions = profile.subdivisions.all()
        departments = profile.departments.all()
    else:
        organizations = []
        subdivisions = []
        departments = []

    # Получаем всех сотрудников
    all_employees = Employee.objects.all().select_related('organization', 'subdivision', 'department')

    # Фильтруем по правам
    filtered_employees = AccessControlHelper.filter_queryset(
        Employee.objects.all(),
        user,
        request
    ).select_related('organization', 'subdivision', 'department')

    context = {
        'user': user,
        'organizations': organizations,
        'subdivisions': subdivisions,
        'departments': departments,
        'all_employees': all_employees,
        'filtered_employees': filtered_employees,
    }

    return render(request, 'debug_permissions.html', context)
