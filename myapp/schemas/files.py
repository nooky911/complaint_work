from pydantic import BaseModel, ConfigDict
from myapp.models.case_files import (
    FileCategory,
    WarrantyDocumentField,
)


class FileInfo(BaseModel):
    """Схема ответа с информацией о файле (для обеих категорий)"""

    id: int
    original_name: str
    mime_type: str
    size_bytes: int
    stored_name: str
    file_path: str
    category: FileCategory
    related_field: WarrantyDocumentField | None = None
    case_id: int

    model_config = ConfigDict(from_attributes=True)
