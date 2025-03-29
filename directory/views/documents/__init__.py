"""
📄 Инициализация пакета представлений для работы с документами

Экспортирует все представления для работы с документами,
чтобы их можно было импортировать из directory.views.documents
"""
from .selection import DocumentSelectionView
from .forms import (
    InternshipOrderFormView,
    AdmissionOrderFormView
)
from .preview import (
    DocumentPreviewView,
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
    'InternshipOrderFormView',
    'AdmissionOrderFormView',
    'DocumentPreviewView',
    'DocumentsPreviewView',
    'update_document_data',
    'GeneratedDocumentListView',
    'GeneratedDocumentDetailView',
    'document_download',
]