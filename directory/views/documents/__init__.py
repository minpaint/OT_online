# directory/views/documents/__init__.py
"""
📄 Инициализация пакета представлений для работы с документами

Экспортирует представления для работы с документами,
которые используются в системе.
"""

from .selection import DocumentSelectionView, get_auto_selected_document_types

# Импортируем только те представления, которые у нас фактически есть
from .management import (
    GeneratedDocumentListView,
    document_download
)

__all__ = [
    'DocumentSelectionView',
    'get_auto_selected_document_types',
    'GeneratedDocumentListView',
    'document_download',
]