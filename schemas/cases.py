from pydantic import BaseModel
from typing import TYPE_CHECKING
from datetime import date, datetime


if TYPE_CHECKING:
    from .warranty import WarrantyWorkResponse

class CaseBase(BaseModel):
    """Основная схема"""
    fault_date: date | None = None
    section_mask: int | None = None
    locomotive_number: str | None = None
    mileage: int | None = None
    component_quantity: int | None = None
    element_quantity: int | None = None
    component_serial_number_old: str | None = None
    component_manufacture_date_old: date | None = None
    element_serial_number_old: str | None = None
    element_manufacture_date_old: date | None = None
    notes: str | None = None
    component_serial_number_new: str | None = None
    component_manufacture_date_new: date | None = None
    element_serial_number_new: str | None = None
    element_manufacture_date_new: date | None = None

    regional_center_id: int | None = None
    locomotive_model_id: int | None = None
    fault_discovered_at_id: int | None = None
    component_equipment_id: int | None = None
    element_equipment_id: int | None = None
    malfunction_id: int | None = None
    repair_type_id: int | None = None
    performed_by_id: int | None = None
    equipment_owner_id: int | None = None
    destination_id: int | None = None
    supplier_id: int | None = None


class CaseCreate(CaseBase):
    """Схема создание случая"""
    fault_date: date
    section_mask: int
    component_quantity: int
    regional_center_id: int
    locomotive_model_id: int
    fault_discovered_at_id: int
    component_equipment_id: int
    malfunction_id: int
    repair_type_id: int


class CaseUpdate(CaseBase):
    """Схема в случае редактирования случая"""
    pass


class CaseList(BaseModel):
    """Схема для списка случаев (превью)"""
    fault_date: date
    section_mask: int
    locomotive_number: str | None = None
    component_quantity: int
    element_quantity: int | None = None
    component_serial_number_old: str | None = None
    component_manufacture_date_old: date | None = None
    element_serial_number_old: str | None = None
    element_manufacture_date_old: date | None = None

    regional_center_id: int
    locomotive_model_id: int
    component_equipment_id: int
    element_equipment_id: int | None = None
    malfunction_id: int
    supplier_id: int | None = None
    status: str

    warranty_work: WarrantyWorkResponse | None = None

    model_config = {"from_attributes": True}


class CaseDetail(BaseModel):
    """Схема для детального просмотра карточки"""
    date_recorded: datetime
    fault_date: date
    section_mask: int
    locomotive_number: str | None
    mileage: int | None
    component_quantity: int
    element_quantity: int | None
    component_serial_number_old: str | None
    component_manufacture_date_old: date | None
    element_serial_number_old: str | None
    element_manufacture_date_old: date | None
    notes: str | None
    component_serial_number_new: str | None
    component_manufacture_date_new: date | None
    element_serial_number_new: str | None
    element_manufacture_date_new: date | None
    regional_center_id: int
    locomotive_model_id: int
    fault_discovered_at_id: int
    component_equipment_id: int
    element_equipment_id: int | None
    malfunction_id: int
    repair_type_id: int
    performed_by_id: int | None
    equipment_owner_id: int | None
    destination_id: int | None
    supplier_id: int | None
    status: str

    warranty_work: WarrantyWorkResponse | None = None

    model_config = {"from_attributes": True}