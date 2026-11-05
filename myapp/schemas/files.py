from pydantic import BaseModel, ConfigDict

from myapp.models.case_files import (
    FileCategory,
    WarrantyDocumentField,
    WaybillDocumentField,
)


class FileInfo(BaseModel):
    """Схема ответа с информацией о файле (для обеих категорий)"""

    id: int
    original_name: str
    mime_type: str
    size_bytes: int
    category: FileCategory
    related_field: WarrantyDocumentField | WaybillDocumentField | None = None
    case_id: int

    model_config = ConfigDict(from_attributes=True)
