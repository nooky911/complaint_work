"""Данные складских документов Omega для API"""

from datetime import datetime

from pydantic import BaseModel


class OmegaStockWarehouse(BaseModel):
    id: int
    sign: str
    name: str


class OmegaReceipt(BaseModel):
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
    parent_lot_movement_number: str | None = None
    original_document_number: str | None = None
    numbered_object: str | None = None
    origin_document_type: str | None = None
    origin_document_date: datetime | None = None


class OmegaStockFile(BaseModel):
    id: int
    name: str
