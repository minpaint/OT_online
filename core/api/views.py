from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ..models import Organization, Department, Division, Position, Employee, Document
from django.shortcuts import get_object_or_404
from .serializers import (
    OrganizationSerializer, DepartmentSerializer, DivisionSerializer,
    PositionSerializer, EmployeeSerializer, DocumentSerializer
)

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

class DivisionViewSet(viewsets.ModelViewSet):
    queryset = Division.objects.all()
    serializer_class = DivisionSerializer

class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

# Добавляем API для зависимых списков
@api_view(['GET'])
def get_departments(request):
    organization_id = request.GET.get('organization')
    if organization_id:
        try:
            departments = Department.objects.filter(
                organization_id=organization_id
            ).order_by('name')
            data = [{
                'id': dept.id,
                'name': str(dept)
            } for dept in departments]
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    return Response([])

@api_view(['GET'])
def get_divisions(request):
    department_id = request.GET.get('department')
    if department_id:
        try:
            department = get_object_or_404(Department, id=department_id)
            divisions = Division.objects.filter(
                department=department,
                department__organization=department.organization
            ).order_by('name')
            data = [{
                'id': div.id,
                'name': str(div)
            } for div in divisions]
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    return Response([])