# deadline_control/urls.py
from django.urls import path, include
from deadline_control.views import equipment, key_deadline, dashboard, medical

app_name = 'deadline_control'

# ⚙️ ТО оборудования
equipment_patterns = [
    path('', equipment.EquipmentListView.as_view(), name='list'),
    path('create/', equipment.EquipmentCreateView.as_view(), name='create'),
    path('<int:pk>/', equipment.EquipmentDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', equipment.EquipmentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', equipment.EquipmentDeleteView.as_view(), name='delete'),
    path('<int:pk>/perform-maintenance/', equipment.perform_maintenance, name='perform_maintenance'),
]

# 📅 Ключевые сроки
key_deadline_patterns = [
    path('', key_deadline.KeyDeadlineListView.as_view(), name='list'),
    path('category/create/', key_deadline.KeyDeadlineCategoryCreateView.as_view(), name='category_create'),
    path('category/<int:pk>/update/', key_deadline.KeyDeadlineCategoryUpdateView.as_view(), name='category_update'),
    path('category/<int:pk>/delete/', key_deadline.KeyDeadlineCategoryDeleteView.as_view(), name='category_delete'),
    path('item/create/', key_deadline.KeyDeadlineItemCreateView.as_view(), name='item_create'),
    path('item/<int:pk>/update/', key_deadline.KeyDeadlineItemUpdateView.as_view(), name='item_update'),
    path('item/<int:pk>/delete/', key_deadline.KeyDeadlineItemDeleteView.as_view(), name='item_delete'),
]

# 🏥 Медицинские осмотры
medical_patterns = [
    path('', medical.MedicalExaminationListView.as_view(), name='list'),
]

urlpatterns = [
    path('', dashboard.DashboardView.as_view(), name='dashboard'),
    path('equipment/', include((equipment_patterns, 'equipment'))),
    path('key-deadlines/', include((key_deadline_patterns, 'key_deadline'))),
    path('medical/', include((medical_patterns, 'medical'))),
]
