from pydantic import BaseModel, ConfigDict, Field

from myapp.schemas.catalogs import MalfunctionResponse, EquipmentName


class EquipmentWithPathResponse(BaseModel):
    """Схема для equipment в выпадающих списках при выборе типа/оборудования/ и т.д."""

    id: int
    name: str
    level: int | None = None
    parent_id: int | None = None
    has_children: bool = False
    supplier_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class EquipmentCreate(BaseModel):
    """Схема для создания нового оборудования"""

    equipment_name: EquipmentName = Field(..., min_length=1)
    parent_id: int | None = None
    supplier_id: int | None = None
    new_supplier_name: str | None = None
    malfunction_ids: list[int] = []
    new_malfunctions: list[str] = []


class EquipmentShortResponse(BaseModel):
    """Схема для ответа при создании оборудования (без вложенных связей)"""

    id: int
    equipment_name: str
    parent_id: int | None = None
    supplier_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class EquipmentResponse(EquipmentShortResponse):
    """Схема для отображения оборудования в ответе (со всеми связями)"""

    malfunctions: list[MalfunctionResponse] = []


class EquipmentUpdate(BaseModel):
    """Схема для частичного обновления оборудования"""

    equipment_name: EquipmentName | None = None
    supplier_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
