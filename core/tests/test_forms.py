from django.test import TestCase
from core.forms import OrganizationForm, EmployeeForm, PositionForm
from core.models import Organization, Position, Division

class OrganizationFormTest(TestCase):
    def test_organization_form_valid(self):
        form_data = {
            'name_ru': 'Тестовая Организация',
            'short_name_ru': 'ТестОрг',
            'name_en': 'Test Organization',
            'short_name_en': 'TestOrg',
            'inn': '1234567890'
        }
        form = OrganizationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_organization_form_invalid(self):
        form_data = {
            'name_ru': '',  # Обязательное поле
            'short_name_ru': 'ТестОрг',
            'inn': '123'  # Неверная длина ИНН
        }
        form = OrganizationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name_ru', form.errors)
        self.assertIn('inn', form.errors)