from pydantic import BaseModel
from datetime import date


class FilterOption(BaseModel):
    id: int
    name: str


class FilterOptionsResponse(BaseModel):
    regional_centers: list[FilterOption]
    locomotive_models: list[FilterOption]
    components: list[FilterOption]
    malfunctions: list[FilterOption]
    suppliers: list[FilterOption]
    repair_types: list[FilterOption]
    statuses: list[str]


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
    repair_type_id: int | None = None
    supplier_id: int | None = None

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
