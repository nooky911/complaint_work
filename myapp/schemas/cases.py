from pydantic import BaseModel, ConfigDict
from datetime import date, datetime

from .references import AuxiliaryItem
from .warranty import WarrantyWorkResponse, WarrantyWorkUpdate


class ParentEquipment(AuxiliaryItem):
    """Схема для родителя, у которой нет вложенного parent"""

    model_config = ConfigDict(from_attributes=True)


class EquipmentItem(AuxiliaryItem):
    """Основная схема оборудования, которая берет только ОДИН уровень родителя"""

    parent: ParentEquipment | None = None
    model_config = ConfigDict(from_attributes=True)


class CaseBase(BaseModel):
    """Основная схема для общих полей, используемых для создания/обновления"""

    # Основные поля данных
    fault_date: date | None = None
    section_mask: int | None = None
    locomotive_number: str | None = None
    mileage: int | None = None
    component_quantity: int | None = None
    element_quantity: int | None = None
    component_serial_number_old: str | None = None
    component_manufacture_date_old: str | None = None
    element_serial_number_old: str | None = None
    element_manufacture_date_old: str | None = None
    notes: str | None = None
    component_serial_number_new: str | None = None
    component_manufacture_date_new: str | None = None
    element_serial_number_new: str | None = None
    element_manufacture_date_new: str | None = None

    # ID-поля
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

    # Вложенная схема для данных о гарантийном ремонте
    warranty_work: WarrantyWorkUpdate | None = None


class CaseUpdate(CaseBase):
    """Схема для обновления случая"""

    warranty_work: WarrantyWorkUpdate | None = None


class CaseOutputData(CaseBase):
    """Схема для вывода"""

    id: int
    date_recorded: datetime
    supplier_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CaseCommonRelations(CaseOutputData):
    """Схема, используется как база для CaseList и CaseDetail"""

    # Объекты-отношения, которые есть и в списке, и в деталях
    regional_center: AuxiliaryItem | None = None
    locomotive_model: AuxiliaryItem | None = None
    component_equipment: EquipmentItem | None = None
    element_equipment: EquipmentItem | None = None
    malfunction: AuxiliaryItem | None = None
    supplier: AuxiliaryItem | None = None
    repair_type: AuxiliaryItem | None = None
    creator_full_name: str | None = None

    status: str | None = None

    warranty_work: WarrantyWorkResponse | None = None


class CaseList(CaseCommonRelations):
    """Схема для списка случаев (превью)"""

    pass


class CaseDetail(CaseCommonRelations):
    """Схема для детального просмотра карточки"""

    # Дополнительные отношения только для детального просмотра
    fault_discovered_at: AuxiliaryItem | None = None
    performed_by: AuxiliaryItem | None = None
    equipment_owner: AuxiliaryItem | None = None
    destination: AuxiliaryItem | None = None
