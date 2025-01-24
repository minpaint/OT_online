from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Organization, Department, Division, Employee, Position

class OrganizationViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.org_data = {
            'name_ru': 'Тестовая Организация',
            'short_name_ru': 'ТестОрг',
            'name_en': 'Test Organization',
            'short_name_en': 'TestOrg',
            'inn': '1234567890'
        }
        self.org = Organization.objects.create(**self.org_data)

    def test_organization_list_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:organization_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/organization_list.html')
        self.assertContains(response, self.org.short_name_ru)

    def test_organization_create_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('core:organization_create'),
            {
                'name_ru': 'Новая Организация',
                'short_name_ru': 'НовОрг',
                'inn': '0987654321'
            }
        )
        self.assertEqual(response.status_code, 302)  # Редирект после создания
        self.assertTrue(
            Organization.objects.filter(short_name_ru='НовОрг').exists()
        )