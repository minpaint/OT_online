from django.urls import path, include
from . import views

app_name = 'core'

urlpatterns = [
    # Существующие URL-паттерны
    path('', views.OrganizationListView.as_view(), name='organization_list'),
    path('organization/add/', views.OrganizationCreateView.as_view(), name='organization_create'),
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('divisions/', views.DivisionListView.as_view(), name='division_list'),
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('positions/', views.PositionListView.as_view(), name='position_list'),
    path('position/add/', views.PositionCreateView.as_view(), name='position_create'),
    path('position/<int:pk>/edit/', views.PositionUpdateView.as_view(), name='position_update'),

    # API URLs
    path('api/', include('core.api.urls')),
]