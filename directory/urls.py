from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from directory.views import (
    HomePageView,          # 🏠 Главная страница
    EmployeeCreateView,    # 👤 Создание сотрудника
    EmployeeUpdateView,    # ✏️ Редактирование сотрудника
    EmployeeDeleteView,    # 🗑️ Удаление сотрудника
    PositionListView,      # 👔 Список должностей
    PositionCreateView,    # ➕ Создание должности
    PositionUpdateView,    # ✏️ Редактирование должности
    PositionDeleteView,    # 🗑️ Удаление должности
    UserRegistrationView,  # 🔐 Регистрация пользователей
)
from directory.autocomplete_views import (
    OrganizationAutocomplete,   # 🏢 Автодополнение организаций
    SubdivisionAutocomplete,      # 🏭 Автодополнение подразделений
    DepartmentAutocomplete,       # 📂 Автодополнение отделов
    PositionAutocomplete,         # 👔 Автодополнение должностей
    DocumentAutocomplete,         # 📄 Автодополнение документов
    EquipmentAutocomplete,        # ⚙️ Автодополнение оборудования
)

app_name = 'directory'

# 🔍 URL-маршруты для автодополнения (DAL)
autocomplete_patterns = [
    path('organization/', OrganizationAutocomplete.as_view(), name='organization-autocomplete'),
    path('subdivision/', SubdivisionAutocomplete.as_view(), name='subdivision-autocomplete'),
    path('department/', DepartmentAutocomplete.as_view(), name='department-autocomplete'),
    path('position/', PositionAutocomplete.as_view(), name='position-autocomplete'),
    path('document/', DocumentAutocomplete.as_view(), name='document-autocomplete'),
    path('equipment/', EquipmentAutocomplete.as_view(), name='equipment-autocomplete'),
]

# 👥 URL-маршруты для сотрудников
employee_patterns = [
    path('create/', EmployeeCreateView.as_view(), name='employee_create'),
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

# 📄 URL-маршруты для документов (если появится соответствующий ListView)
document_patterns = [
    # path('', DocumentListView.as_view(), name='document_list'),
]

# ⚙️ URL-маршруты для оборудования (если появится соответствующий ListView)
equipment_patterns = [
    # path('', EquipmentListView.as_view(), name='equipment_list'),
]

# 🔐 URL-маршруты для аутентификации
auth_patterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='directory:auth:login'
    ), name='logout'),

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
    path('documents/', include((document_patterns, 'documents'))),  # Если появятся документы
    path('equipment/', include((equipment_patterns, 'equipment'))),  # Если появится оборудование
]
