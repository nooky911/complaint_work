from pydantic import BaseModel
from datetime import date
from .references import AuxiliaryItem, RepairTypeItem


class FilterOptionsResponse(BaseModel):
    """Схема для фильтров - ВСЕ возможные поля фильтрации"""

    # Все справочники из формы
    regional_centers: list[AuxiliaryItem]
    locomotive_models: list[AuxiliaryItem]
    fault_discovered_at: list[AuxiliaryItem]
    malfunctions: list[AuxiliaryItem]
    suppliers: list[AuxiliaryItem]
    repair_types: list[RepairTypeItem]
    equipment_owners: list[AuxiliaryItem]
    performed_by: list[AuxiliaryItem]
    destinations: list[AuxiliaryItem]

    # Оборудование
    components: list[AuxiliaryItem]
    elements: list[AuxiliaryItem]
    new_components: list[AuxiliaryItem]
    new_elements: list[AuxiliaryItem]

    # Статус
    statuses: list[str]

    # Дополнительно для документации
    notification_summaries: list[AuxiliaryItem]
    response_summaries: list[AuxiliaryItem]
    decision_summaries: list[AuxiliaryItem]


class CaseFilterParams(BaseModel):
    """Схема параметров для фильтрации случаев"""

    # Фильтры REPAIR_CASE_EQUIPMENT

    # Даты
    date_from: date | None = None
    date_to: date | None = None

    # Идентификаторы
    regional_center_id: int | None = None
    locomotive_model_id: int | None = None
    component_equipment_id: int | None = None
    element_equipment_id: int | None = None
    malfunction_id: int | None = None
    new_component_equipment_id: int | None = None
    new_element_equipment_id: int | None = None
    repair_type_id: int | None = None
    supplier_id: int | None = None
    user_id: int | None = None

    # Числа/Строки
    section_mask: int | None = None
    locomotive_number: str | None = None
    component_serial_number_old: str | None = None
    element_serial_number_old: str | None = None
    component_serial_number_new: str | None = None
    element_serial_number_new: str | None = None

    # Статус
    status: str | None = None

    # Фильтры WARRANTY_WORK

    # Уведомления
    notification_number: str | None = None
    notification_date: date | None = None
    re_notification_number: str | None = None
    re_notification_date: date | None = None

    # Ответы
    response_letter_number: str | None = None
    response_letter_date: date | None = None

    # Акты
    claim_act_number: str | None = None
    claim_act_date: date | None = None
    work_completion_act_number: str | None = None
    work_completion_act_date: date | None = None

    # Содержания
    notification_summary_id: int | None = None
    response_summary_id: int | None = None
    decision_summary_id: int | None = None

    # Пагинация
    skip: int = 0
    limit: int = 50
