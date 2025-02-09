from django.urls import path, include
from directory.views import (
    HomeView,
    EmployeeListView,
    EmployeeCreateView,
    EmployeeUpdateView,
    EmployeeDeleteView,
    PositionListView,
    PositionCreateView,
    PositionUpdateView,
    PositionDeleteView,
)
from directory.autocomplete_views import (
    OrganizationAutocomplete,
    SubdivisionAutocomplete,
    DepartmentAutocomplete,
    PositionAutocomplete,
    DocumentAutocomplete,
    EquipmentAutocomplete,
)

app_name = 'directory'

# 🔍 Маршруты для автодополнения (DAL)
autocomplete_patterns = [
    path(
        'organization/',
        OrganizationAutocomplete.as_view(),
        name='organization-autocomplete'
    ),
    path(
        'subdivision/',
        SubdivisionAutocomplete.as_view(),
        name='subdivision-autocomplete'
    ),
    path(
        'department/',
        DepartmentAutocomplete.as_view(),
        name='department-autocomplete'
    ),
    path(
        'position/',
        PositionAutocomplete.as_view(),
        name='position-autocomplete'
    ),
    path(
        'document/',
        DocumentAutocomplete.as_view(),
        name='document-autocomplete'
    ),
    path(
        'equipment/',
        EquipmentAutocomplete.as_view(),
        name='equipment-autocomplete'
    ),
]

# 👥 Маршруты для сотрудников
employee_patterns = [
    path('', EmployeeListView.as_view(), name='employee_list'),
    path('create/', EmployeeCreateView.as_view(), name='employee_create'),
    path('<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee_delete'),
]

# 👔 Маршруты для должностей
position_patterns = [
    path('', PositionListView.as_view(), name='position_list'),
    path('create/', PositionCreateView.as_view(), name='position_create'),
    path('<int:pk>/update/', PositionUpdateView.as_view(), name='position_update'),
    path('<int:pk>/delete/', PositionDeleteView.as_view(), name='position_delete'),
]

# Основные URL маршруты
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('autocomplete/', include(autocomplete_patterns)),
    path('employees/', include(employee_patterns)),
    path('positions/', include(position_patterns)),
]