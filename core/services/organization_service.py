from typing import List, Optional
from django.db.models import Q
from core.models import Organization

class OrganizationService:
    @staticmethod
    def get_organizations(search_term: Optional[str] = None) -> List[Organization]:
        """
        Получить список организаций с возможностью поиска
        """
        queryset = Organization.objects.all()

        if search_term:
            queryset = queryset.filter(
                Q(name_ru__icontains=search_term) |
                Q(short_name_ru__icontains=search_term) |
                Q(inn__icontains=search_term)
            )

        return queryset.order_by('short_name_ru')

    @staticmethod
    def get_organization_by_id(organization_id: int) -> Optional[Organization]:
        """
        Получить организацию по ID
        """
        try:
            return Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            return None

    @staticmethod
    def create_organization(data: dict) -> Organization:
        """
        Создать новую организацию
        """
        return Organization.objects.create(**data)

    @staticmethod
    def update_organization(organization: Organization, data: dict) -> Organization:
        """
        Обновить данные организации
        """
        for key, value in data.items():
            setattr(organization, key, value)
        organization.save()
        return organization

    @staticmethod
    def delete_organization(organization: Organization) -> bool:
        """
        Удалить организацию
        """
        try:
            organization.delete()
            return True
        except Exception:
            return False
