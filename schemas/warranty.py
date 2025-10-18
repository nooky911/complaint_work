from pydantic import BaseModel
from datetime import date


class WarrantyWorkBase(BaseModel):
    """Основная схема"""
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


class WarrantyWorkCreate(WarrantyWorkBase):
    """Схема для создания"""
    pass


class WarrantyWorkUpdate(WarrantyWorkBase):
    """Схема для редактирования"""
    pass


class WarrantyWorkResponse(WarrantyWorkBase):
    """Схема для отображения"""

    model_config = {"from_attributes": True}
