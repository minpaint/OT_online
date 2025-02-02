from django.urls import path
from . import views
from .ajax import (
    get_subdivisions,
    get_departments,
    get_positions,
    get_documents,
    get_equipment
)
from .views import (
    EmployeeListView,
    EmployeeCreateView,
    EmployeeUpdateView,
    EmployeeDeleteView,
    PositionListView,
    PositionCreateView,
    PositionUpdateView,
    PositionDeleteView,
)

app_name = 'directory'

urlpatterns = [
    # AJAX URLs
    path('ajax/subdivisions/', get_subdivisions, name='ajax_subdivisions'),
    path('ajax/departments/', get_departments, name='ajax_departments'),
    path('ajax/positions/', get_positions, name='ajax_positions'),
    path('ajax/documents/', get_documents, name='ajax_documents'),
    path('ajax/equipment/', get_equipment, name='ajax_equipment'),

    # Employee URLs
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    path('employees/create/', EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee_delete'),

    # Position URLs
    path('positions/', PositionListView.as_view(), name='position_list'),
    path('positions/create/', PositionCreateView.as_view(), name='position_create'),
    path('positions/<int:pk>/update/', PositionUpdateView.as_view(), name='position_update'),
    path('positions/<int:pk>/delete/', PositionDeleteView.as_view(), name='position_delete'),
]