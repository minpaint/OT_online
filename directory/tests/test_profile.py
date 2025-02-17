from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from directory.models import Organization, Employee, Position


class HomePageViewTests(TestCase):
    def setUp(self):
        """Подготовка данных для тестов"""
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

        # Привязываем организацию к пользователю
        self.user.profile.organizations.add(self.org)
        self.client.login(username='testuser', password='testpass123')

    def test_home_page_not_authenticated(self):
        """Тест доступа к главной странице без аутентификации"""
        self.client.logout()
        response = self.client.get(reverse('directory:home'))
        self.assertEqual(response.status_code, 302)

    def test_home_page_authenticated(self):
        """Тест доступа к главной странице с аутентификацией"""
        response = self.client.get(reverse('directory:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'directory/home.html')

    def test_employee_hiring_form(self):
        """Тест формы приема на работу"""
        form_data = {
            'full_name_nominative': 'Иванов Иван Иванович',
            'full_name_dative': 'Иванову Ивану Ивановичу',
            'date_of_birth': '1990-01-01',
            'organization': self.org.id,
            'position': self.position.id,
            'place_of_residence': 'г. Минск',
            'preview': False
        }

        response = self.client.post(reverse('directory:home'), form_data)
        self.assertRedirects(response, reverse('directory:home'))

        # Проверяем создание сотрудника
        self.assertEqual(Employee.objects.count(), 1)
        employee = Employee.objects.first()
        self.assertEqual(employee.full_name_nominative, 'Иванов Иван Иванович')

    def test_preview_mode(self):
        """Тест режима предпросмотра"""
        form_data = {
            'full_name_nominative': 'Иванов Иван Иванович',
            'full_name_dative': 'Иванову Ивану Ивановичу',
            'date_of_birth': '1990-01-01',
            'organization': self.org.id,
            'position': self.position.id,
            'place_of_residence': 'г. Минск',
            'preview': True
        }

        response = self.client.post(reverse('directory:home'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'directory/preview.html')