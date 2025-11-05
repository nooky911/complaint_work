from pydantic import BaseModel, ConfigDict
from datetime import date

from .references import AuxiliaryItem


class WarrantyWorkBase(BaseModel):
    """Основная схема рекламационной работы"""

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


class WarrantyWorkUpdate(WarrantyWorkBase):
    """Схема для редактирования рекламационной работы"""

    pass


class WarrantyWorkResponse(WarrantyWorkBase):
    """Схема для отображения рекламационной работы"""

    id: int
    case_id: int

    notification_summary: AuxiliaryItem | None = None
    response_summary: AuxiliaryItem | None = None
    decision_summary: AuxiliaryItem | None = None

    model_config = ConfigDict(from_attributes=True)
