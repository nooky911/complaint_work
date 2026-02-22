from pydantic import BaseModel
from datetime import date
from .references import AuxiliaryItem, RepairTypeItem


class FilterOptionsResponse(BaseModel):
    """Справочники, которые прилетят на фронт для заполнения выпадающих списков"""

    regional_centers: list[AuxiliaryItem]
    locomotive_models: list[AuxiliaryItem]
    fault_discovered_at: list[AuxiliaryItem]
    malfunctions: list[AuxiliaryItem]
    suppliers: list[AuxiliaryItem]
    repair_types: list[RepairTypeItem]
    equipment_owners: list[AuxiliaryItem]
    performed_by: list[AuxiliaryItem]
    destinations: list[AuxiliaryItem]
    components: list[AuxiliaryItem]
    elements: list[AuxiliaryItem]
    new_components: list[AuxiliaryItem]
    new_elements: list[AuxiliaryItem]
    statuses: list[str]
    notification_summaries: list[AuxiliaryItem]
    response_summaries: list[AuxiliaryItem]
    decision_summaries: list[AuxiliaryItem]
    locomotive_numbers: list[str]
    notification_numbers: list[str]
    notification_dates: list[date]
    re_notification_dates: list[date]
    response_letter_dates: list[date]
    claim_act_dates: list[date]
    work_completion_act_dates: list[date]
    component_serial_numbers: list[str]
    element_serial_numbers: list[str]
    notes: list[str]
    users: list[AuxiliaryItem]


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
