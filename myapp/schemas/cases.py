from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from myapp.services import CaseValidationError
from .references import AuxiliaryItem, EquipmentItem
from .warranty import WarrantyWorkResponse, WarrantyWorkUpdate
from .waybill import WaybillDocResponse, WaybillDocUpdate


class PassportLinkInput(BaseModel):
    """Выбранный неисправный экземпляр паспорта"""

    node_id: int = Field(gt=0)
    role: Literal["component", "element"]
    parent_node_id: int | None = None
    version: int | None = None


class PassportReplacementInput(BaseModel):
    """Данные установленного экземпляра оборудования"""

    node_id: int = Field(gt=0)
    version: int | None = None
    equipment_id: int | None = None
    serial_number: str | None = Field(default=None, max_length=255)
    manufacture_date_text: str | None = Field(default=None, max_length=100)


class CaseBase(BaseModel):
    """Основная схема для общих полей, используемых для создания/обновления"""

    passport_links: list[PassportLinkInput] | None = None
    replacement_items: list[PassportReplacementInput] | None = None
    expected_revision: int | None = None

    # Основные поля данных
    fault_date: date | None = None
    section_mask: int | None = None
    locomotive_number: str | None = None
    passport_id: int | None = None
    mileage: int | None = None
    component_quantity: int | None = None
    element_quantity: int | None = None
    new_component_quantity: int | None = None
    new_element_quantity: int | None = None
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
    new_component_equipment_id: int | None = None
    new_element_equipment_id: int | None = None
    repair_type_id: int | None = None
    performed_by_id: int | None = None
    equipment_owner_id: int | None = None
    destination_id: int | None = None

    model_config = ConfigDict(from_attributes=True)

    def validate_write(self) -> None:
        """Проверяет общие правила записи без ограничений чтения старых данных"""
        data = self.model_dump(exclude_unset=True)
        for field in (
            "component_manufacture_date_old", "element_manufacture_date_old",
            "component_manufacture_date_new", "element_manufacture_date_new",
        ):
            value = data.get(field)
            if value is not None and any(character.isalpha() for character in value):
                raise CaseValidationError(field)
        for item in self.replacement_items or []:
            value = item.manufacture_date_text
            if value and any(character.isalpha() for character in value):
                raise CaseValidationError("replacement_items")
        if "fault_date" in data:
            if self.fault_date is None or not 2000 <= self.fault_date.year or self.fault_date > date.today():
                raise CaseValidationError("fault_date", "Укажите дату неисправности с 2000 года, не позже сегодняшней")
        if self.mileage is not None and self.mileage < 0:
            raise CaseValidationError("mileage", "Пробег не может быть отрицательным")
        for field in ("component_quantity", "element_quantity", "new_component_quantity", "new_element_quantity"):
            value = getattr(self, field)
            if value is not None and value < 1:
                raise CaseValidationError(field, "Количество выбранного оборудования должно быть не меньше 1")
        if "component_quantity" in data and self.component_quantity is None:
            raise CaseValidationError("component_quantity", "Укажите количество выбранного оборудования")
        warranty = getattr(self, "warranty_work", None)
        if warranty is not None:
            warranty.validate_dates(self.fault_date)
        waybill = getattr(self, "waybill_doc", None)
        if waybill is not None:
            waybill.validate_dates()


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

    user_id: int | None = None

    warranty_work: WarrantyWorkUpdate | None = None
    waybill_doc: WaybillDocUpdate | None = None


class CaseUpdate(CaseBase):
    """Схема для обновления случая"""

    user_id: int | None = None
    warranty_work: WarrantyWorkUpdate | None = None
    waybill_doc: WaybillDocUpdate | None = None


class UserPreview(BaseModel):
    id: int
    login: str
    full_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CaseOutputData(CaseBase):
    """Схема для вывода"""

    passport_links: list[dict] = Field(default_factory=list)
    replacement_items: list[dict] = Field(default_factory=list)
    revision: int = 1
    created_by_id: int | None = None
    created_by_name: str | None = None
    creator_source: str | None = None

    id: int
    locomotive_identity_locked: bool = False
    date_recorded: datetime
    supplier_id: int | None = None
    user_id: int
    user: UserPreview | None = None
    locked_by_id: int | None = None
    lock_expires_at: datetime | None = None
    locked_by: UserPreview | None = None

    display_number: int | None = None


class CaseCommonRelations(CaseOutputData):
    """Схема, используется как база для CaseList и CaseDetail"""

    # Объекты-отношения, которые есть и в списке, и в деталях
    regional_center: AuxiliaryItem | None = None
    locomotive_model: AuxiliaryItem | None = None
    component_equipment: EquipmentItem | None = None
    element_equipment: EquipmentItem | None = None
    malfunction: AuxiliaryItem | None = None
    new_component_equipment: EquipmentItem | None = None
    new_element_equipment: EquipmentItem | None = None
    supplier: AuxiliaryItem | None = None
    repair_type: AuxiliaryItem | None = None
    creator_full_name: str | None = None

    status: str | None = None

    warranty_work: WarrantyWorkResponse | None = None
    waybill_doc: WaybillDocResponse | None = None


class CaseList(CaseCommonRelations):
    """Схема для списка случаев (превью)"""

    pass


class PaginatedCaseListResponse(BaseModel):
    """Схема ответа для пагинированного списка случаев"""

    items: list[CaseList]
    total: int


class CaseDetail(CaseCommonRelations):
    """Схема для детального просмотра карточки"""

    # Дополнительные отношения только для детального просмотра
    fault_discovered_at: AuxiliaryItem | None = None
    performed_by: AuxiliaryItem | None = None
    equipment_owner: AuxiliaryItem | None = None
    destination: AuxiliaryItem | None = None


class SupplierPreviewRequest(BaseModel):
    """Схема для динамического обновления поставщика"""

    equipment_id: int | None
    locomotive_number: str | None
    locomotive_model_id: int | None
