from pydantic import BaseModel, ConfigDict
from myapp.models.case_files import (
    FileCategory,
    WarrantyDocumentField,
)


class FileBase(BaseModel):
    """Базовая схема с общими полями"""

    original_name: str
    mime_type: str
    size_bytes: int


class PrimaryFileUploadRequest(BaseModel):
    """Схема для загрузки первичной документации"""

    pass


class WarrantyFileUploadRequest(BaseModel):
    """Схема для загрузки файлов для рекламационной работы"""

    related_field: WarrantyDocumentField


class FileInfo(FileBase):
    """Схема ответа с информацией о файле (для обеих категорий)"""

    id: int
    stored_name: str
    file_path: str
    category: FileCategory
    related_field: WarrantyDocumentField | None = None
    case_id: int

    model_config = ConfigDict(from_attributes=True)
