from pydantic import BaseModel, ConfigDict, Field


class MalfunctionUpdate(BaseModel):
    """Схема для редактирования неисправности"""

    defect_name: str | None = None


class MalfunctionResponse(BaseModel):
    """Схема для отображения неисправности в ответе"""

    id: int
    defect_name: str
    model_config = ConfigDict(from_attributes=True)


class MalfunctionAttachRequest(BaseModel):
    """Схема для добавления неисправностей"""

    malfunction_ids: list[int] = []
    new_names: list[str] = []


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

    equipment_name: str = Field(..., min_length=1)
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

    equipment_name: str | None = None
    supplier_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class SupplierUpdate(BaseModel):
    """Схема обновления Поставщика"""

    supplier_name: str | None = None


class SupplierResponse(BaseModel):
    """Схема для ответа при редактировании Поставщика"""

    id: int
    supplier_name: str

    model_config = ConfigDict(from_attributes=True)


class SupplierCreate(BaseModel):
    """Схема для создания Поставщика уже у имеющегося оборудования"""

    supplier_name: str
