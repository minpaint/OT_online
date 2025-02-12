from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from directory.models import Organization, Employee, Position


class EmployeeTests(TestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Создаем тестовую организацию
        self.org = Organization.objects.create(
            full_name_ru="Тестовая организация",
            short_name_ru="ТестОрг",
            full_name_by="Тэставая арганізацыя",
            short_name_by="ТэстАрг"
        )

        # Создаем тестовую должность
        self.position = Position.objects.create(
            position_name="Тестовая должность",
            organization=self.org
        )

        self.user.profile.organizations.add(self.org)
        self.client.login(username='testuser', password='testpass123')

    def test_employee_list_view(self):
        """Тест списка сотрудников"""
        response = self.client.get(reverse('directory:employee_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'directory/employees/list.html')

    def test_employee_create_view(self):
        """Тест создания сотрудника"""
        form_data = {
            'full_name_nominative': 'Иванов Иван Иванович',
            'full_name_dative': 'Иванову Ивану Ивановичу',
            'date_of_birth': '1990-01-01',
            'organization': self.org.id,
            'position': self.position.id,
            'place_of_residence': 'г. Минск'
        }

        response = self.client.post(
            reverse('directory:employee_create'),
            form_data
        )

        self.assertRedirects(
            response,
            reverse('directory:employee_list'),
            status_code=302
        )

    def test_employee_update_view(self):
        """Тест обновления сотрудника"""
        employee = Employee.objects.create(
            full_name_nominative='Тест Тестович',
            full_name_dative='Тесту Тестовичу',
            date_of_birth='1990-01-01',
            organization=self.org,
            position=self.position,
            place_of_residence='г. Минск'
        )

        form_data = {
            'full_name_nominative': 'Новый Тест Тестович',
            'full_name_dative': 'Новому Тесту Тестовичу',
            'date_of_birth': '1990-01-01',
            'organization': self.org.id,
            'position': self.position.id,
            'place_of_residence': 'г. Минск'
        }

        response = self.client.post(
            reverse('directory:employee_update', kwargs={'pk': employee.pk}),
            form_data
        )

        self.assertRedirects(
            response,
            reverse('directory:employee_list'),
            status_code=302
        )