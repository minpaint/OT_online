from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.contrib.auth import logout

from .views import siz
from .views import siz_issued  # 👈 Добавляем импорт модуля siz_issued

# Импортируем представления из новой модульной структуры документов
from directory.views.documents import (
    DocumentSelectionView,
    InternshipOrderFormView,
    AdmissionOrderFormView,
    DocumentPreviewView,
    DocumentsPreviewView, # Временно закомментировано, пока не реализованы все функции
    update_document_data,
    GeneratedDocumentListView,
    GeneratedDocumentDetailView,
    document_download
)

from directory.views import (
    HomePageView,  # 🏠 Главная страница
    EmployeeListView,  # 👥 Список сотрудников
    EmployeeCreateView,  # 👤 Создание сотрудника
    EmployeeUpdateView,  # ✏️ Редактирование сотрудника
    EmployeeDeleteView,  # 🗑️ Удаление сотрудника
    EmployeeHiringView,  # 👥 Найм сотрудника - добавляем импорт
    PositionListView,  # 👔 Список должностей
    PositionCreateView,  # ➕ Создание должности
    PositionUpdateView,  # ✏️ Редактирование должности
    PositionDeleteView,  # 🗑️ Удаление должности
    UserRegistrationView,  # 🔐 Регистрация пользователей
)

from directory.autocomplete_views import (
    OrganizationAutocomplete,  # 🏢 Автодополнение организаций
    SubdivisionAutocomplete,  # 🏭 Автодополнение подразделений
    DepartmentAutocomplete,  # 📂 Автодополнение отделов
    PositionAutocomplete,  # 👔 Автодополнение должностей
    DocumentAutocomplete,  # 📄 Автодополнение документов
    EquipmentAutocomplete,  # ⚙️ Автодополнение оборудования
    SIZAutocomplete,  # 🛡️ Автодополнение СИЗ
)

app_name = 'directory'

# 🔄 Добавляем собственное представление для выхода из системы
def logout_view(request):
    """🚪 Выход из системы с редиректом на страницу входа"""
    logout(request)
    return redirect('directory:auth:login')

# 🔍 URL-маршруты для автодополнения (DAL)
autocomplete_patterns = [
    path('organization/', OrganizationAutocomplete.as_view(), name='organization-autocomplete'),
    path('subdivision/', SubdivisionAutocomplete.as_view(), name='subdivision-autocomplete'),
    path('department/', DepartmentAutocomplete.as_view(), name='department-autocomplete'),
    path('position/', PositionAutocomplete.as_view(), name='position-autocomplete'),
    path('document/', DocumentAutocomplete.as_view(), name='document-autocomplete'),
    path('equipment/', EquipmentAutocomplete.as_view(), name='equipment-autocomplete'),
    path('siz/', SIZAutocomplete.as_view(), name='siz-autocomplete'),
]

# 👥 URL-маршруты для сотрудников
employee_patterns = [
    path('', EmployeeListView.as_view(), name='employee_list'),
    path('create/', EmployeeCreateView.as_view(), name='employee_create'),
    path('hire/', EmployeeHiringView.as_view(), name='employee_hire'),  # Новый маршрут
    path('<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee_delete'),
]

# 👔 URL-маршруты для должностей
position_patterns = [
    path('', PositionListView.as_view(), name='position_list'),
    path('create/', PositionCreateView.as_view(), name='position_create'),
    path('<int:pk>/update/', PositionUpdateView.as_view(), name='position_update'),
    path('<int:pk>/delete/', PositionDeleteView.as_view(), name='position_delete'),
]

# 📄 URL-маршруты для документов - обновлены для новой модульной структуры
document_patterns = [
    path('', GeneratedDocumentListView.as_view(), name='document_list'),
    path('<int:pk>/', GeneratedDocumentDetailView.as_view(), name='document_detail'),
    path('<int:pk>/download/', document_download, name='document_download'),
    path('selection/<int:employee_id>/', DocumentSelectionView.as_view(), name='document_selection'),
    path('internship-order/<int:employee_id>/', InternshipOrderFormView.as_view(), name='internship_order_form'),
    path('admission-order/<int:employee_id>/', AdmissionOrderFormView.as_view(), name='admission_order_form'),
    path('preview/', DocumentPreviewView.as_view(), name='document_preview'),
    path('documents-preview/', DocumentsPreviewView.as_view(), name='documents_preview'),  # Временно закомментировано
    path('api/update-preview-data/', update_document_data, name='update_preview_data'),
]

# ⚙️ URL-маршруты для оборудования (если появится соответствующий ListView)
equipment_patterns = [
    # path('', EquipmentListView.as_view(), name='equipment_list'),
]

# 🛡️ URL-маршруты для СИЗ
siz_patterns = [
    path('', siz.SIZListView.as_view(), name='siz_list'),
    path('norms/create/', siz.SIZNormCreateView.as_view(), name='siznorm_create'),
    path('norms/api/', siz.siz_by_position_api, name='siz_api'),
    # 🆕 Добавляем новые маршруты для выдачи СИЗ
    path('personal-card/<int:employee_id>/pdf/', siz_issued.export_personal_card_pdf, name='siz_personal_card_pdf'),
    path('issue-selected/<int:employee_id>/', siz_issued.issue_selected_siz, name='issue_selected_siz'),
    # Добавляем этот маршрут
    path('issue/', siz_issued.SIZIssueFormView.as_view(), name='siz_issue'),
    path('issue/employee/<int:employee_id>/', siz_issued.SIZIssueFormView.as_view(), name='siz_issue_for_employee'),
    path('personal-card/<int:employee_id>/', siz_issued.SIZPersonalCardView.as_view(), name='siz_personal_card'),
    path('return/<int:siz_issued_id>/', siz_issued.SIZIssueReturnView.as_view(), name='siz_return'),
]

# 🔐 URL-маршруты для аутентификации
auth_patterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    # 🔄 Исправление: используем собственное представление вместо LogoutView
    path('logout/', logout_view, name='logout'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    # URL для сброса пароля
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             success_url=reverse_lazy('directory:auth:password_reset_done')
         ),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url=reverse_lazy('directory:auth:password_reset_complete')
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]

# 🌐 Основные URL маршруты
urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('auth/', include((auth_patterns, 'auth'))),
    path('autocomplete/', include(autocomplete_patterns)),
    path('employees/', include((employee_patterns, 'employees'))),
    path('positions/', include((position_patterns, 'positions'))),
    path('documents/', include((document_patterns, 'documents'))),
    path('equipment/', include((equipment_patterns, 'equipment'))),
    path('positions/<int:position_id>/siz-norms/', siz.position_siz_norms, name='position_siz_norms'),
    path('siz/', include((siz_patterns, 'siz'))),

    # API эндпоинты для работы с личной карточкой СИЗ
    path('api/positions/<int:position_id>/siz-norms/', siz.get_position_siz_norms, name='api_position_siz_norms'),
    path('api/employees/<int:employee_id>/issued-siz/', siz.get_employee_issued_siz, name='api_employee_issued_siz'),
    path('api/siz/<int:siz_id>/', siz.get_siz_details, name='api_siz_details'),
    path('api/employees/<int:employee_id>/issued-siz/', siz_issued.employee_siz_issued_list, name='api_employee_issued_siz'),
]