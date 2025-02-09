# 📁 directory/urls.py
from django.urls import path, include
from . import views
from .ajax import (
    get_subdivisions,
    get_departments,
    get_positions,
    get_documents,
    get_equipment
)
from .views import (
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

app_name = 'directory'

ajax_patterns = [
    path('subdivisions/', get_subdivisions, name='ajax_subdivisions'),
    path('departments/', get_departments, name='ajax_departments'),
    path('positions/', get_positions, name='ajax_positions'),
    path('documents/', get_documents, name='ajax_documents'),
    path('equipment/', get_equipment, name='ajax_equipment'),
]

employee_patterns = [
    path('', EmployeeListView.as_view(), name='employee_list'),
    path('create/', EmployeeCreateView.as_view(), name='employee_create'),
    path('<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee_delete'),
]

position_patterns = [
    path('', PositionListView.as_view(), name='position_list'),
    path('create/', PositionCreateView.as_view(), name='position_create'),
    path('<int:pk>/update/', PositionUpdateView.as_view(), name='position_update'),
    path('<int:pk>/delete/', PositionDeleteView.as_view(), name='position_delete'),
]

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('ajax/', include(ajax_patterns)),
    path('employees/', include(employee_patterns)),
    path('positions/', include(position_patterns)),
]
