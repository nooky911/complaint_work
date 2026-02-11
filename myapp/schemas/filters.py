from pydantic import BaseModel
from datetime import date
from fastapi import Query
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
    component_serial_numbers: list[str]
    element_serial_numbers: list[str]
    notes: list[str]


class CaseFilterParams(BaseModel):
    """Параметры фильтрации: ПО ВСЕМ ПОЛЯМ (кроме кол-ва и дат пр-ва оборудования)"""

    skip: int = 0
    limit: int = 50

    # Даты неисправности
    date_from: date | None = None
    date_to: date | None = None

    # Идентификаторы (RepairCaseEquipment)
    regional_center_id: list[int] | None = Query(None)
    locomotive_model_id: list[int] | None = Query(None)
    component_equipment_id: list[int] | None = Query(None)
    element_equipment_id: list[int] | None = Query(None)
    malfunction_id: list[int] | None = Query(None)
    repair_type_id: list[int] | None = Query(None)
    supplier_id: list[int] | None = Query(None)
    equipment_owner_id: list[int] | None = Query(None)
    performed_by_id: list[int] | None = Query(None)
    destination_id: list[int] | None = Query(None)

    # Строки (RepairCaseEquipment)
    section_mask: int | None = None
    locomotive_number: list[str] | None = Query(None)
    component_serial_number_old: list[str] | None = Query(None)
    element_serial_number_old: list[str] | None = Query(None)
    component_serial_number_new: list[str] | None = Query(None)
    element_serial_number_new: list[str] | None = Query(None)
    notes: list[str] | None = Query(None)

    # Статус
    status: list[str] | None = Query(None)

    # --- WARRANTY WORK (Документация) ---
    # Номера документов
    notification_number: list[str] | None = Query(None)
    re_notification_number: list[str] | None = Query(None)
    response_letter_number: list[str] | None = Query(None)
    claim_act_number: list[str] | None = Query(None)
    work_completion_act_number: list[str] | None = Query(None)

    # Даты документов
    notification_date: list[date] | None = Query(None)
    re_notification_date: list[date] | None = Query(None)
    response_letter_date: list[date] | None = Query(None)
    claim_act_date: list[date] | None = Query(None)
    work_completion_act_date: list[date] | None = Query(None)

    # Содержания (ID)
    notification_summary_id: list[int] | None = Query(None)
    response_summary_id: list[int] | None = Query(None)
    decision_summary_id: list[int] | None = Query(None)
