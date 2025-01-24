from django.test import TestCase
from core.models import Organization, Employee, Division, Position, Department
from core.services.organization_service import OrganizationService
from core.services.employee_service import EmployeeService

class OrganizationServiceTest(TestCase):
    def setUp(self):
        self.org_data = {
            'name_ru': 'Тестовая Организация',
            'short_name_ru': 'ТестОрг',
            'inn': '1234567890'
        }
        self.organization = Organization.objects.create(**self.org_data)

    def test_get_organizations(self):
        organizations = OrganizationService.get_organizations()
        self.assertEqual(organizations.count(), 1)
        self.assertEqual(organizations[0], self.organization)

    def test_create_organization(self):
        new_org_data = {
            'name_ru': 'Новая Организация',
            'short_name_ru': 'НовОрг',
            'inn': '0987654321'
        }
        new_org = OrganizationService.create_organization(new_org_data)
        self.assertEqual(new_org.short_name_ru, 'НовОрг')
        self.assertEqual(Organization.objects.count(), 2)