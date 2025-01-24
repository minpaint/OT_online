from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from core.models import Organization, Department
from core.api.serializers import OrganizationSerializer, DepartmentSerializer

class OrganizationAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.org_data = {
            'name_ru': 'Тестовая Организация',
            'short_name_ru': 'ТестОрг',
            'inn': '1234567890'
        }
        self.org = Organization.objects.create(**self.org_data)

    def test_get_organizations(self):
        url = reverse('organization-list')
        response = self.client.get(url)
        organizations = Organization.objects.all()
        serializer = OrganizationSerializer(organizations, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], serializer.data)