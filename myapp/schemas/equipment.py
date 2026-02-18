from pydantic import BaseModel, ConfigDict
from .references import AuxiliaryItem


class EquipmentWithPathResponse(BaseModel):
    """Схема для equipment в выпадающих списках при выборе типа/оборудования/ и т.д."""

    id: int
    name: str
    parent_id: int | None = None
    has_children: bool = False
    supplier_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ParentEquipment(AuxiliaryItem):
    """Схема для родителя, у которой нет вложенного parent"""

    model_config = ConfigDict(from_attributes=True)


class EquipmentItem(AuxiliaryItem):
    """Основная схема оборудования, которая берет только ОДИН уровень родителя"""

    parent: ParentEquipment | None = None
    model_config = ConfigDict(from_attributes=True)
