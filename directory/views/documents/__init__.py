"""
📄 Инициализация пакета представлений для работы с документами

Экспортирует все представления для работы с документами,
чтобы их можно было импортировать из directory.views.documents
"""

from .selection import DocumentSelectionView

from .forms import (
    AllOrdersFormView,  # Исправлено: импортируем представления, а не формы
    SIZCardFormView     # Исправлено: импортируем представления, а не формы
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
    'AllOrdersFormView',  # Исправлено: экспортируем представления, а не формы
    'SIZCardFormView',    # Исправлено: экспортируем представления, а не формы
    'DocumentsPreviewView',
    'update_document_data',
    'GeneratedDocumentListView',
    'GeneratedDocumentDetailView',
    'document_download',
]