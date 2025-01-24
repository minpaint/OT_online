from django.test import TestCase
from django.core.exceptions import ValidationError
from core.models import Organization, Department, Division, Position, Employee, Document

class OrganizationModelTest(TestCase):
    def setUp(self):
        self.org_data = {
            'name_ru': 'Тестовая Организация',
            'short_name_ru': 'ТестОрг',
            'name_en': 'Test Organization',
            'short_name_en': 'TestOrg',
            'inn': '1234567890'
        }

    def test_organization_creation(self):
        org = Organization.objects.create(**self.org_data)
        self.assertEqual(org.name_ru, self.org_data['name_ru'])
        self.assertEqual(org.inn, self.org_data['inn'])

    def test_organization_str(self):
        org = Organization.objects.create(**self.org_data)
        self.assertEqual(str(org), self.org_data['short_name_ru'])

    def test_invalid_inn(self):
        self.org_data['inn'] = '123'  # Неверная длина ИНН
        with self.assertRaises(ValidationError):
            org = Organization(**self.org_data)
            org.full_clean()

class EmployeeModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name_ru='Тестовая Организация',
            short_name_ru='ТестОрг',
            inn='1234567890'
        )
        self.dept = Department.objects.create(
            name='Тестовый отдел',
            organization=self.org
        )
        self.div = Division.objects.create(
            name='Тестовое подразделение',
            department=self.dept
        )
        self.position = Position.objects.create(
            name='Тестовая должность'
        )
        self.employee_data = {
            'last_name': 'Иванов',
            'first_name': 'Иван',
            'middle_name': 'Иванович',
            'position': self.position,
            'division': self.div
        }

    def test_employee_creation(self):
        employee = Employee.objects.create(**self.employee_data)
        self.assertEqual(employee.last_name, self.employee_data['last_name'])
        self.assertEqual(employee.division, self.div)

    def test_employee_full_name(self):
        employee = Employee.objects.create(**self.employee_data)
        expected_full_name = 'Иванов Иван Иванович'
        self.assertEqual(employee.full_name, expected_full_name)

class PositionModelTest(TestCase):
    def setUp(self):
        self.position_data = {
            'name': 'Электрик',
            'is_electrical_personnel': True,
            'electrical_safety_group': 3,
            'is_internship_supervisor': True,
            'internship_period': 10
        }

    def test_position_creation(self):
        position = Position.objects.create(**self.position_data)
        self.assertEqual(position.name, self.position_data['name'])
        self.assertTrue(position.is_electrical_personnel)
        self.assertEqual(position.electrical_safety_group, 3)

    def test_invalid_safety_group(self):
        self.position_data['electrical_safety_group'] = 6  # Недопустимая группа
        with self.assertRaises(ValidationError):
            position = Position(**self.position_data)
            position.full_clean()