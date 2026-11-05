import re
from typing import Annotated
from pydantic import BaseModel, ConfigDict, AfterValidator


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


def validate_equipment_name(value):
    """Запрещает пробельные символы в наименованиях классификатора"""
    if re.search(r"\s", value):
        raise ValueError('В наименовании оборудования используйте "_" вместо пробелов')
    return value


EquipmentName = Annotated[str, AfterValidator(validate_equipment_name)]
