from pydantic import BaseModel
from pydantic import Field
from datetime import date
from .references import AuxiliaryItem, RepairTypeItem


class FilterOptionsResponse(BaseModel):
    """Справочники, которые прилетят на фронт для заполнения выпадающих списков"""

    regional_centers: list[AuxiliaryItem] = Field(default_factory=list)
    locomotive_models: list[AuxiliaryItem] = Field(default_factory=list)
    fault_discovered_at: list[AuxiliaryItem] = Field(default_factory=list)
    malfunctions: list[AuxiliaryItem] = Field(default_factory=list)
    suppliers: list[AuxiliaryItem] = Field(default_factory=list)
    repair_types: list[RepairTypeItem] = Field(default_factory=list)
    equipment_owners: list[AuxiliaryItem] = Field(default_factory=list)
    performed_by: list[AuxiliaryItem] = Field(default_factory=list)
    destinations: list[AuxiliaryItem] = Field(default_factory=list)
    components: list[AuxiliaryItem] = Field(default_factory=list)
    elements: list[AuxiliaryItem] = Field(default_factory=list)
    new_components: list[AuxiliaryItem] = Field(default_factory=list)
    new_elements: list[AuxiliaryItem] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    notification_summaries: list[AuxiliaryItem] = Field(default_factory=list)
    response_summaries: list[AuxiliaryItem] = Field(default_factory=list)
    decision_summaries: list[AuxiliaryItem] = Field(default_factory=list)
    locomotive_numbers: list[str] = Field(default_factory=list)
    notification_numbers: list[str] = Field(default_factory=list)
    notification_dates: list[date] = Field(default_factory=list)
    re_notification_dates: list[date] = Field(default_factory=list)
    response_letter_dates: list[date] = Field(default_factory=list)
    claim_act_dates: list[date] = Field(default_factory=list)
    work_completion_act_dates: list[date] = Field(default_factory=list)
    component_serial_numbers: list[str] = Field(default_factory=list)
    element_serial_numbers: list[str] = Field(default_factory=list)
    component_serial_numbers_new: list[str] = Field(default_factory=list)
    element_serial_numbers_new: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    users: list[AuxiliaryItem] = Field(default_factory=list)


class CaseFilterParams(BaseModel):
    """Параметры фильтрации: ПО ВСЕМ ПОЛЯМ (кроме кол-ва и дат пр-ва оборудования)"""

    skip: int = 0
    limit: int = 50

    # Даты неисправности
    date_from: date | None = None
    date_to: date | None = None

    # Идентификаторы (RepairCaseEquipment)
    regional_center_id: list[int] | None = None
    locomotive_model_id: list[int] | None = None
    component_equipment_id: list[int] | None = None
    element_equipment_id: list[int] | None = None
    malfunction_id: list[int] | None = None
    repair_type_id: list[int] | None = None
    supplier_id: list[int] | None = None
    equipment_owner_id: list[int] | None = None
    performed_by_id: list[int] | None = None
    destination_id: list[int] | None = None

    # Новое оборудование (установленное при ремонте)
    new_component_equipment_id: list[int] | None = None
    new_element_equipment_id: list[int] | None = None

    # Строки (RepairCaseEquipment)
    section_mask: int | None = None
    locomotive_number: list[str] | None = None
    component_serial_number_old: list[str] | None = None
    element_serial_number_old: list[str] | None = None
    component_serial_number_new: list[str] | None = None
    element_serial_number_new: list[str] | None = None
    notes: list[str] | None = None

    # Статус
    status: list[str] | None = None

    # --- WARRANTY WORK (Документация) ---
    notification_number: list[str] | None = None
    re_notification_number: list[str] | None = None
    response_letter_number: list[str] | None = None
    claim_act_number: list[str] | None = None
    work_completion_act_number: list[str] | None = None

    notification_date: list[date] | None = None
    re_notification_date: list[date] | None = None
    response_letter_date: list[date] | None = None
    claim_act_date: list[date] | None = None
    work_completion_act_date: list[date] | None = None

    notification_summary_id: list[int] | None = None
    response_summary_id: list[int] | None = None
    decision_summary_id: list[int] | None = None
    user_id: list[int] | None = None
