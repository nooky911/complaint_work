from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

from myapp.schemas.cases import PassportLinkInput


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
    article: str | None
    designation: str | None
    serial_number: str | None
    manufacture_date: date | str | None
    install_date: date | None
    manufacturer: str | None
    supplier: str | None
    supplier_id: int | None
    equipment_id: int | None
    version: int = 1
    has_history: bool = False


class ProductPassportResponse(BaseModel):
    """Паспорт с импортированными узлами"""

    id: int
    product_type: str
    locomotive_model_id: int
    locomotive_model_name: str
    product_number: str
    omega_name: str
    commissioned_at: date
    imported_at: datetime
    nodes: list[ProductPassportNodeResponse]

    model_config = ConfigDict(from_attributes=True)


class PassportReplacementPreview(BaseModel):
    """Данные для расчёта состава замены по случаю"""

    fault_date: date | None = None
    section_mask: int
    component_equipment_id: int
    element_equipment_id: int | None = None
    repair_type_id: int
    case_id: int | None = None
    passport_links: list[PassportLinkInput]


class PassportCorrection(BaseModel):
    """Данные ручного исправления позиции паспорта"""

    expected_version: int
    reason: str = Field(min_length=1, max_length=2000)
    equipment_id: int | None = None
    serial_number: str | None = Field(default=None, max_length=255)
    manufacture_date_text: str | None = Field(default=None, max_length=100)
