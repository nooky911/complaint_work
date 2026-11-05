from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class OmegaStockColumnFilter(BaseModel):
    """Режим и значения фильтра колонки складских документов"""

    mode: Literal["include", "exclude"]
    values: list[str | None]


class OmegaStockFilterRequest(BaseModel):
    """Набор фильтров для поиска складских документов"""

    filters: dict[str, OmegaStockColumnFilter] = Field(default_factory=dict)


class OmegaStockCaseFilterRequest(OmegaStockFilterRequest):
    """Направление и фильтры случаев для привязки общего складского документа"""

    direction: Literal["loco", "train"] = "loco"


class OmegaStockCaseSearchRequest(OmegaStockFilterRequest):
    """Фильтры случаев и выбранные строки для сортировки перед пагинацией"""

    direction: Literal["loco", "train"] = "loco"
    selected_ids: list[int] = Field(default_factory=list, max_length=10000)


class OmegaStockWarehouse(BaseModel):
    """Краткие данные склада Omega"""

    id: int
    sign: str
    name: str


class OmegaReceipt(BaseModel):
    """Данные приходного ордера Omega"""

    document_id: int
    number: str
    accompanying_date: datetime | None = None
    warehouse: str
    supplier: str | None = None
    accompanying_number: str | None = None
    accounting_date: datetime | None = None
    note: str | None = None
    created_at: datetime | None = None
    created_by: str | None = None
    updated_at: datetime | None = None


class OmegaInplantInvoice(BaseModel):
    """Данные внутризаводской накладной Omega"""

    document_id: int
    document_date: datetime
    status: str
    number: str
    note: str | None = None
    warehouse: str
    accepted_by: str | None = None
    recipient: str | None = None
    issued_by: str | None = None


class OmegaOutboundInvoice(BaseModel):
    """Данные накладной на сторону Omega"""

    document_id: int
    number: str
    warehouse: str
    recipient: str | None = None
    document_date: datetime
    shipping_date: datetime | None = None
    status: str
    created_at: datetime | None = None
    has_files: bool
    created_by: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None


class OmegaStockItem(BaseModel):
    """Позиция оборудования в составе складского документа"""

    item_id: int
    lot_movement_id: int | None = None
    position: int | None = None
    card_number: str | None = None
    nomenclature: str | None = None
    nominal_number: str | None = None
    document_quantity: float | None = None
    quantity: float | None = None
    unit: str | None = None
    depot_card: str | None = None
    price_rub: float | None = None
    vat_rub: float | None = None
    total_with_vat: float | None = None
    party_number: str | None = None
    sender_card: str | None = None
    receiver_card: str | None = None
    invoice_number: str | None = None
    invoice_date: datetime | None = None
    sender_warehouse: str | None = None
    sender_sign: str | None = None
    item_note: str | None = None
    lot_movement_number: str | None = None
    original_document_number: str | None = None
    origin_document_date: datetime | None = None


class OmegaStockFile(BaseModel):
    """Идентификатор и имя вложения складского документа"""

    id: int
    name: str


class OmegaStockCaseLinkRequest(BaseModel):
    """Выбранные случаи и данные существующего блока передвижения"""

    direction: Literal["loco", "train"] = "loco"
    case_ids: list[int] = Field(min_length=1, max_length=100)
    related_field: Literal[
        "ttn_replacement", "ttn_from_rc", "ttn_to_supplier", "ttn_from_supplier"
    ]
    number: str = Field(max_length=50)
    document_date: str
    provider_id: int | None = None
    preview_token: str | None = None
    confirm_overwrite: bool = False
