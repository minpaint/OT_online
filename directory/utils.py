from django.db.models import Q
from directory.models import StructuralSubdivision


def get_subdivision_tree(organization_id):
    """Получает дерево подразделений для организации."""
    return StructuralSubdivision.objects.filter(
        organization_id=organization_id
    ).select_related('parent_subdivision')


def get_child_subdivisions(subdivision_id):
    """Рекурсивно получает все дочерние подразделения."""
    subdivisions = []
    children = StructuralSubdivision.objects.filter(parent_subdivision_id=subdivision_id)

    for child in children:
        subdivisions.append(child)
        subdivisions.extend(get_child_subdivisions(child.id))

    return subdivisions


def search_employees(query):
    """Поиск сотрудников по различным критериям."""
    return Q(full_name_nominative__icontains=query) | \
        Q(full_name_dative__icontains=query) | \
        Q(position__position_name__icontains=query) | \
        Q(structural_subdivision__name__icontains=query)