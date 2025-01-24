from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # OrganizationalUnit URLs
    path('structure/',
         views.OrganizationalStructureView.as_view(),
         name='organizational_structure'),
    path('units/',
         views.OrganizationalUnitListView.as_view(),
         name='organizational_unit_list'),
    path('units/create/',
         views.OrganizationalUnitCreateView.as_view(),
         name='organizational_unit_create'),
    path('units/<int:pk>/update/',
         views.OrganizationalUnitUpdateView.as_view(),
         name='organizational_unit_update'),
    path('units/<int:pk>/delete/',
         views.OrganizationalUnitDeleteView.as_view(),
         name='organizational_unit_delete'),

    # Organization URLs
    path('organizations/',
         views.OrganizationListView.as_view(),
         name='organization_list'),
    path('organizations/create/',
         views.OrganizationCreateView.as_view(),
         name='organization_create'),
    path('organizations/<int:pk>/update/',
         views.OrganizationUpdateView.as_view(),
         name='organization_update'),
    path('organizations/<int:pk>/delete/',
         views.OrganizationDeleteView.as_view(),
         name='organization_delete'),

    # Position URLs
    path('positions/',
         views.PositionListView.as_view(),
         name='position_list'),
    path('positions/create/',
         views.PositionCreateView.as_view(),
         name='position_create'),
    path('positions/<int:pk>/update/',
         views.PositionUpdateView.as_view(),
         name='position_update'),
    path('positions/<int:pk>/delete/',
         views.PositionDeleteView.as_view(),
         name='position_delete'),

    # Employee URLs
    path('employees/',
         views.EmployeeListView.as_view(),
         name='employee_list'),
    path('employees/create/',
         views.EmployeeCreateView.as_view(),
         name='employee_create'),
    path('employees/<int:pk>/update/',
         views.EmployeeUpdateView.as_view(),
         name='employee_update'),
    path('employees/<int:pk>/delete/',
         views.EmployeeDeleteView.as_view(),
         name='employee_delete'),

    # Document URLs
    path('documents/',
         views.DocumentListView.as_view(),
         name='document_list'),
    path('documents/create/',
         views.DocumentCreateView.as_view(),
         name='document_create'),
    path('documents/<int:pk>/update/',
         views.DocumentUpdateView.as_view(),
         name='document_update'),
    path('documents/<int:pk>/delete/',
         views.DocumentDeleteView.as_view(),
         name='document_delete'),
    path('documents/<int:pk>/download/',
         views.DocumentDownloadView.as_view(),
         name='document_download'),
]