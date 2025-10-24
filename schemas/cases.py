from pydantic import BaseModel, ConfigDict, Field
from typing import TYPE_CHECKING
from datetime import date, datetime

from .references import AuxiliaryItem

if TYPE_CHECKING:
    from .warranty import WarrantyWorkResponse


class CaseBase(BaseModel):
    """Основная схема для общих полей и ID, используемых для создания/обновления"""
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
    """Схема для редактирования случая"""
    pass


class CaseOutputData(BaseModel):
    """Промежуточная схема для ВСЕХ полей данных (без ID)"""
    id: int
    fault_date: date
    section_mask: int
    locomotive_number: str | None = None
    mileage: int | None = None
    component_quantity: int
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

    model_config = ConfigDict(from_attributes=True)


class CaseCommonRelations(CaseOutputData):
    """Схема, используется как база для CaseList и CaseDetail"""
    regional_center: AuxiliaryItem
    locomotive_model: AuxiliaryItem
    component_equipment: AuxiliaryItem
    element_equipment: AuxiliaryItem | None = None
    malfunction: AuxiliaryItem
    supplier: AuxiliaryItem | None = None

    status: str = Field(..., validation_alias='calculated_status')

    warranty_work: "WarrantyWorkResponse | None" = None


class CaseList(CaseCommonRelations):
    """Схема для списка случаев (превью)"""
    pass


class CaseDetail(CaseCommonRelations):
    """Схема для детального просмотра карточки"""
    date_recorded: datetime

    fault_discovered_at: AuxiliaryItem
    repair_type: AuxiliaryItem
    performed_by: AuxiliaryItem | None = None
    equipment_owner: AuxiliaryItem | None = None
    destination: AuxiliaryItem | None = None