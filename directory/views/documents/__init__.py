# D:\YandexDisk\OT_online\directory\views\documents\__init__.py
"""
📄 Инициализация пакета представлений для работы с документами

Экспортирует все представления для работы с документами,
чтобы их можно было импортировать из directory.views.documents
"""
from .selection import DocumentSelectionView
from .forms import (
    AllOrdersForm,
    SIZCardForm  # Добавляем новую форму
)
from .preview import (
    DocumentsPreviewView,
    update_document_data
)
from .management import (
    GeneratedDocumentListView,
    GeneratedDocumentDetailView,
    document_download
)

__all__ = [
    'DocumentSelectionView',
    'AllOrdersForm',
    'SIZCardForm',  # Добавляем новую форму в список экспорта
    'DocumentsPreviewView',
    'update_document_data',
    'GeneratedDocumentListView',
    'GeneratedDocumentDetailView',
    'document_download',
]