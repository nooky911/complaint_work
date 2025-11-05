from pydantic import BaseModel, ConfigDict


class EquipmentWithPathResponse(BaseModel):
    """Схема для equipment в выпадающих списках при выборе типа/оборудования/ и т.д."""

    id: int
    name: str
    level: int
    has_children: bool
    supplier_id: int | None

    model_config = ConfigDict(from_attributes=True)
