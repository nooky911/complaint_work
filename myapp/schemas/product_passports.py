from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class ProductPassportModelResponse(BaseModel):
    """Модель локомотива, для которой есть паспорта"""

    id: int
    name: str


class ProductPassportSearchItem(BaseModel):
    """Краткие данные паспорта для результата поиска"""

    id: int
    product_number: str
    omega_name: str


class ProductPassportNodeResponse(BaseModel):
    """Узел сохранённого дерева паспорта"""

    id: int
    parent_id: int | None
    tree_name: str
    full_name: str | None
    peshka: str | None
    designation: str | None
    serial_number: str | None
    manufacture_date: date | None
    install_date: date | None
    manufacturer: str | None
    supplier: str | None
    supplier_id: int | None
    equipment_id: int | None


class ProductPassportResponse(BaseModel):
    """Паспорт с импортированными узлами"""

    id: int
    product_type: str
    locomotive_model_id: int
    locomotive_model_name: str
    product_number: str
    omega_name: str
    imported_at: datetime
    nodes: list[ProductPassportNodeResponse]

    model_config = ConfigDict(from_attributes=True)
