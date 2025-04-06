"""
📄 Инициализация пакета представлений для работы с документами

Экспортирует все представления для работы с документами,
чтобы их можно было импортировать из directory.views.documents
"""

from .selection import DocumentSelectionView

# Убираем импорт из forms, т.к. мы решили не реализовывать эти формы
# from .forms import AllOrdersFormView, SIZCardFormView

# Мы также убираем preview, т.к. мы решили не реализовывать эту функциональность
# from .preview import DocumentsPreviewView, update_document_data

from .management import (
    GeneratedDocumentListView,
    GeneratedDocumentDetailView,
    document_download
)

__all__ = [
    'DocumentSelectionView',
    'GeneratedDocumentListView',
    'GeneratedDocumentDetailView',
    'document_download',
]