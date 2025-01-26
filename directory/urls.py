from django.urls import path
from directory.views import (
    HomeView,
    EmployeeListView, EmployeeCreateView, EmployeeUpdateView, EmployeeDeleteView,
    PositionListView, PositionCreateView, PositionUpdateView, PositionDeleteView,
    get_subdivisions, get_positions,get_departments
)

app_name = 'directory'

urlpatterns = [
    # Главная страница
    path('', HomeView.as_view(), name='home'),

    # Сотрудники
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/add/', EmployeeCreateView.as_view(), name='employee-create'),
    path('employees/<int:pk>/edit/', EmployeeUpdateView.as_view(), name='employee-update'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee-delete'),

    # Должности
    path('positions/', PositionListView.as_view(), name='position-list'),
    path('positions/add/', PositionCreateView.as_view(), name='position-create'),
    path('positions/<int:pk>/edit/', PositionUpdateView.as_view(), name='position-update'),
    path('positions/<int:pk>/delete/', PositionDeleteView.as_view(), name='position-delete'),

    # AJAX endpoints
    path('api/subdivisions/', get_subdivisions, name='api-subdivisions'),
    path('api/positions/', get_positions, name='api-positions'),
    path('api/departments/', get_departments, name='api-departments'),
]