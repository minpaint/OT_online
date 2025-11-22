from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.contrib.auth import logout
from .views import siz
from .views import siz_issued
from directory.views import commissions
from directory.views.documents.siz_integration import generate_siz_card_docx_view
from directory.views import (
    HomePageView,
    IntroductoryBriefingView,  # 📺 Вводный инструктаж
    EmployeeListView,
    EmployeeCreateView,
    EmployeeUpdateView,
    EmployeeDeleteView,
    EmployeeProfileView,  # ← добавлено
    EmployeeHiringView,
    PositionListView,
    PositionCreateView,
    PositionUpdateView,
    PositionDeleteView,
    UserRegistrationView,
    hiring,  # 📑 Импортируем модуль с представлениями приемов на работу
    employees,
)
from deadline_control.views import medical_examination  # 🏥 Импортируем модуль с представлениями медосмотров

from directory.views.employees import EmployeeTreeView

from directory.views import quiz_views  # 📝 Импортируем модуль с представлениями экзаменов
from directory.views import quiz_import_views  # 📥 Импорт вопросов
from directory.views.debug_permissions import debug_permissions_view  # Отладка прав

from directory.views.documents import (
    DocumentSelectionView,
    GeneratedDocumentListView,
    document_download,
    PeriodicProtocolView,
)


from directory.autocomplete_views import (
    OrganizationAutocomplete,
    SubdivisionAutocomplete,
    DepartmentAutocomplete,
    PositionAutocomplete,
    DocumentAutocomplete,
    EquipmentAutocomplete,
    SIZAutocomplete,
    EmployeeByCommissionAutocomplete,
    EmployeeForCommissionAutocomplete,
    CommissionAutocomplete,
)

from directory.views.hiring import (
    HiringTreeView, HiringListView, HiringDetailView, HiringCreateView, HiringUpdateView,
    HiringDeleteView, CreateHiringFromEmployeeView, SimpleHiringView, position_requirements_api
)

app_name = 'directory'


def logout_view(request):
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
    path('employee/', EmployeeByCommissionAutocomplete.as_view(), name='employee-autocomplete'),
    path('employee-for-commission/', EmployeeForCommissionAutocomplete.as_view(),
         name='employee-for-commission-autocomplete'),
    path('commission/', CommissionAutocomplete.as_view(), name='commission-autocomplete'),
]

# 👥 Сотрудники
employee_patterns = [
    path('', EmployeeTreeView.as_view(), name='employee_list'),  # 🌳 Древовидное представление по умолчанию
    path('table/', EmployeeListView.as_view(), name='employee_list_table'),  # 📋 Табличное представление
    path('create/', EmployeeCreateView.as_view(), name='employee_create'),
    path('hire/', EmployeeHiringView.as_view(), name='employee_hire'),
    path('<int:pk>/', EmployeeProfileView.as_view(), name='employee_profile'),  # ← добавлено
    path('<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee_delete'),
]

# 👔 Должности
position_patterns = [
    path('', PositionListView.as_view(), name='position_list'),
    path('create/', PositionCreateView.as_view(), name='position_create'),
    path('<int:pk>/update/', PositionUpdateView.as_view(), name='position_update'),
    path('<int:pk>/delete/', PositionDeleteView.as_view(), name='position_delete'),
]

# 📄 Документы
document_patterns = [
    path('', GeneratedDocumentListView.as_view(), name='document_list'),
    path('selection/<int:employee_id>/', DocumentSelectionView.as_view(), name='document_selection'),
    path('periodic-protocol/', PeriodicProtocolView.as_view(), name='periodic_protocol'),
    path('<int:pk>/download/', document_download, name='document_download'),
]

# 🛡 Комиссии
commission_patterns = [
    path('', commissions.CommissionTreeView.as_view(), name='commission_list'),
    path('create/', commissions.CommissionCreateView.as_view(), name='commission_create'),
    path('<int:pk>/', commissions.CommissionDetailView.as_view(), name='commission_detail'),
    path('<int:pk>/update/', commissions.CommissionUpdateView.as_view(), name='commission_update'),
    path('<int:pk>/delete/', commissions.CommissionDeleteView.as_view(), name='commission_delete'),
    path('<int:commission_id>/member/add/', commissions.CommissionMemberCreateView.as_view(),
         name='commission_member_add'),
    path('member/<int:pk>/update/', commissions.CommissionMemberUpdateView.as_view(), name='commission_member_update'),
    path('member/<int:pk>/delete/', commissions.CommissionMemberDeleteView.as_view(), name='commission_member_delete'),
]

# 🛡️ СИЗ
siz_patterns = [
    path('', siz.SIZListView.as_view(), name='siz_list'),
    path('norms/create/', siz.SIZNormCreateView.as_view(), name='siznorm_create'),
    path('norms/api/', siz.siz_by_position_api, name='siz_api'),
    path('issue-selected/<int:employee_id>/', siz_issued.issue_selected_siz, name='issue_selected_siz'),
    path('issue/', siz_issued.SIZIssueFormView.as_view(), name='siz_issue'),
    path('issue/employee/<int:employee_id>/', siz_issued.SIZIssueFormView.as_view(), name='siz_issue_for_employee'),
    path('personal-card/<int:employee_id>/', siz_issued.SIZPersonalCardView.as_view(), name='siz_personal_card'),
    path('return/<int:siz_issued_id>/', siz_issued.SIZIssueReturnView.as_view(), name='siz_return'),
    path('siz/siz-card/<int:employee_id>/', generate_siz_card_docx_view, name='siz_card'),
]

# 📑 Приемы на работу
hiring_patterns = [
    path('', hiring.HiringTreeView.as_view(), name='hiring_tree'),
    path('list/', hiring.HiringListView.as_view(), name='hiring_list'),
    path('<int:pk>/', hiring.HiringDetailView.as_view(), name='hiring_detail'),
    path('create/', hiring.HiringCreateView.as_view(), name='hiring_create'),
    path('<int:pk>/update/', hiring.HiringUpdateView.as_view(), name='hiring_update'),
    path('<int:pk>/delete/', hiring.HiringDeleteView.as_view(), name='hiring_delete'),
    path('create-from-employee/<int:employee_id>/', hiring.CreateHiringFromEmployeeView.as_view(),
         name='create_from_employee'),

    # 🧙‍♂️ форма приема (единый маршрут вместо трех отдельных)
    path('simple/', SimpleHiringView.as_view(), name='simple_hiring'),

    # API для проверки требований должности
    path('api/position/<int:position_id>/requirements/', position_requirements_api, name='position_requirements_api'),
]

# 📝 Экзамены (тестирование по охране труда)
quiz_patterns = [
    path('', quiz_views.quiz_list, name='quiz_list'),
    path('home/', quiz_views.exam_home, name='exam_home'),  # Главная страница exam поддомена
    # Итоговый экзамен (без category_id)
    path('<int:quiz_id>/start/', quiz_views.quiz_start, name='quiz_start'),
    # Тренировка по разделу (с category_id)
    path('<int:quiz_id>/start/category/<int:category_id>/', quiz_views.quiz_start, name='quiz_start_category'),
    path('<int:attempt_id>/question/<int:question_number>/', quiz_views.quiz_question, name='quiz_question'),
    path('<int:attempt_id>/answer/<int:question_id>/', quiz_views.quiz_answer, name='quiz_answer'),
    path('<int:attempt_id>/result/', quiz_views.quiz_result, name='quiz_result'),
    path('history/', quiz_views.quiz_history, name='quiz_history'),
    path('category/<int:category_id>/', quiz_views.category_detail, name='category_detail'),
    # Доступ по токену
    path('access/<uuid:token>/', quiz_views.token_access, name='token_access'),
    # Импорт вопросов
    path('import/', quiz_import_views.quiz_import_upload, name='quiz_import_upload'),
    path('import/preview/', quiz_import_views.quiz_import_preview, name='quiz_import_preview'),
    path('import/cancel/', quiz_import_views.quiz_import_cancel, name='quiz_import_cancel'),
]

# 🏥 Медосмотры
medical_patterns = [
    # Виды медосмотров
    path('exam-types/', medical_examination.MedicalExaminationTypeListView.as_view(), name='medical_examination_types'),
    path('exam-types/add/', medical_examination.MedicalExaminationTypeCreateView.as_view(),
         name='medical_examination_type_create'),
    path('exam-types/<int:pk>/edit/', medical_examination.MedicalExaminationTypeUpdateView.as_view(),
         name='medical_examination_type_update'),
    path('exam-types/<int:pk>/delete/', medical_examination.MedicalExaminationTypeDeleteView.as_view(),
         name='medical_examination_type_delete'),

    # Вредные факторы
    path('harmful-factors/', medical_examination.HarmfulFactorListView.as_view(), name='harmful_factors'),
    path('harmful-factors/<int:pk>/', medical_examination.HarmfulFactorDetailView.as_view(),
         name='harmful_factor_detail'),
    path('harmful-factors/add/', medical_examination.HarmfulFactorCreateView.as_view(), name='harmful_factor_create'),
    path('harmful-factors/<int:pk>/edit/', medical_examination.HarmfulFactorUpdateView.as_view(),
         name='harmful_factor_update'),
    path('harmful-factors/<int:pk>/delete/', medical_examination.HarmfulFactorDeleteView.as_view(),
         name='harmful_factor_delete'),

    # Нормы медосмотров
    path('norms/', medical_examination.MedicalNormListView.as_view(), name='medical_norms'),
    path('norms/add/', medical_examination.MedicalNormCreateView.as_view(), name='medical_norm_create'),
    path('norms/<int:pk>/edit/', medical_examination.MedicalNormUpdateView.as_view(), name='medical_norm_update'),
    path('norms/<int:pk>/delete/', medical_examination.MedicalNormDeleteView.as_view(), name='medical_norm_delete'),
    path('norms/import/', medical_examination.MedicalNormImportView.as_view(), name='medical_norm_import'),
    path('norms/export/', medical_examination.MedicalNormExportView.as_view(), name='medical_norm_export'),

    # Медосмотры сотрудников
    path('exams/', medical_examination.EmployeeMedicalExaminationListView.as_view(), name='employee_exams'),
    path('exams/<int:pk>/', medical_examination.EmployeeMedicalExaminationDetailView.as_view(),
         name='employee_exam_detail'),
    path('exams/add/', medical_examination.EmployeeMedicalExaminationCreateView.as_view(), name='employee_exam_create'),
    path('exams/<int:pk>/edit/', medical_examination.EmployeeMedicalExaminationUpdateView.as_view(),
         name='employee_exam_update'),
    path('exams/<int:pk>/delete/', medical_examination.EmployeeMedicalExaminationDeleteView.as_view(),
         name='employee_exam_delete'),
    path('tabs/employee/<int:employee_id>/exams/', medical_examination.EmployeeMedicalExaminationTabView.as_view(),
         name='employee_exams_tab'),
]


# 🔐 Аутентификация
auth_patterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', UserRegistrationView.as_view(), name='register'),

    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        success_url=reverse_lazy('directory:auth:password_reset_done')
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url=reverse_lazy('directory:auth:password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]

# 🌐 Основные маршруты
urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('introductory-briefing/', IntroductoryBriefingView.as_view(), name='introductory_briefing'),
    path('debug-permissions/', debug_permissions_view, name='debug_permissions'),  # Отладка
    path('auth/', include((auth_patterns, 'auth'))),
    path('autocomplete/', include(autocomplete_patterns)),
    path('employees/', include((employee_patterns, 'employees'))),
    path('positions/', include((position_patterns, 'positions'))),
    path('documents/', include((document_patterns, 'documents'))),
    path('positions/<int:position_id>/siz-norms/', siz.position_siz_norms, name='position_siz_norms'),
    path('siz/', include((siz_patterns, 'siz'))),
    path('commissions/', include((commission_patterns, 'commissions'))),
    path('hiring/', include((hiring_patterns, 'hiring'))),
    path('medical/', include((medical_patterns, 'medical'))),  # 🏥 Добавляем маршруты для медосмотров
    path('quiz/', include((quiz_patterns, 'quiz'))),  # 📝 Добавляем маршруты для экзаменов

    # API для СИЗ
    path('api/positions/<int:position_id>/siz-norms/', siz.get_position_siz_norms, name='api_position_siz_norms'),
    path('api/employees/<int:employee_id>/issued-siz/', siz.get_employee_issued_siz, name='api_employee_issued_siz'),
    path('api/siz/<int:siz_id>/', siz.get_siz_details, name='api_siz_details'),
    path('api/employees/<int:employee_id>/issued-siz/', siz_issued.employee_siz_issued_list,
         name='api_employee_issued_siz'),

    # API для медосмотров
    path('api/medical/employee/<int:employee_id>/status/', medical_examination.api_employee_medical_status,
         name='api_employee_medical_status'),
    path('api/medical/position/<int:position_id>/norms/', medical_examination.api_position_medical_norms,
         name='api_position_medical_norms'),
    path('api/subdivisions/', employees.get_subdivisions, name='api-subdivisions'),
]
