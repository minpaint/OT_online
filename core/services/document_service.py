from typing import List, Optional
from django.db.models import Q
from core.models import Document

class DocumentService:
    @staticmethod
    def get_documents(search_term: Optional[str] = None) -> List[Document]:
        """
        Получить список документов с возможностью поиска
        """
        queryset = Document.objects.all()

        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(document_type__icontains=search_term)
            )

        return queryset.order_by('-created_at')

    @staticmethod
    def get_document_by_id(document_id: int) -> Optional[Document]:
        """
        Получить документ по ID
        """
        try:
            return Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return None

    @staticmethod
    def create_document(data: dict) -> Document:
        """
        Создать новый документ
        """
        return Document.objects.create(**data)

    @staticmethod
    def update_document(document: Document, data: dict) -> Document:
        """
        Обновить данные документа
        """
        for key, value in data.items():
            setattr(document, key, value)
        document.save()
        return document

    @staticmethod
    def delete_document(document: Document) -> bool:
        """
        Удалить документ
        """
        try:
            document.delete()
            return True
        except Exception:
            return False
