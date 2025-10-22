from pydantic import BaseModel, ConfigDict, Field
from typing import TYPE_CHECKING
from datetime import date, datetime
from .references import AuxiliaryItem

if TYPE_CHECKING:
    from .warranty import WarrantyWorkResponse


class CaseBase(BaseModel):
    """Основная схема для общих полей и ID, используемых для создания/обновления."""
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

    # ID-поля для создания/обновления
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

    model_config = ConfigDict(from_attributes=True)


class CaseCreate(CaseBase):
    """Схема создание случая (переопределение обязательных полей)."""
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
    """Схема для редактирования случая."""
    pass


class CaseList(BaseModel):
    """Схема для списка случаев (превью)"""
    id: int
    fault_date: date
    section_mask: int
    locomotive_number: str | None = None
    component_quantity: int
    element_quantity: int | None = None
    component_serial_number_old: str | None = None
    component_manufacture_date_old: date | None = None
    element_serial_number_old: str | None = None
    element_manufacture_date_old: date | None = None

    regional_center: AuxiliaryItem
    locomotive_model: AuxiliaryItem
    component_equipment: AuxiliaryItem
    element_equipment: AuxiliaryItem | None = None
    malfunction: AuxiliaryItem
    supplier: AuxiliaryItem | None = None

    status: str = Field(..., validation_alias='calculated_status')

    warranty_work: "WarrantyWorkResponse | None" = None

    model_config = ConfigDict(from_attributes=True)


class CaseDetail(BaseModel):
    """Схема для детального просмотра карточки"""
    id: int
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

    # Вложенные объекты (справочники)
    regional_center: AuxiliaryItem
    locomotive_model: AuxiliaryItem
    fault_discovered_at: AuxiliaryItem
    component_equipment: AuxiliaryItem
    element_equipment: AuxiliaryItem | None = None
    malfunction: AuxiliaryItem
    repair_type: AuxiliaryItem
    performed_by: AuxiliaryItem | None = None
    equipment_owner: AuxiliaryItem | None = None
    destination: AuxiliaryItem | None = None
    supplier: AuxiliaryItem | None = None

    status: str = Field(..., validation_alias='calculated_status')

    warranty_work: "WarrantyWorkResponse | None" = None

    model_config = ConfigDict(from_attributes=True)