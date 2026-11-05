from pydantic import BaseModel, ConfigDict
from datetime import date

from myapp.services import CaseValidationError
from .references import AuxiliaryItem


class WarrantyWorkBase(BaseModel):
    """Базовая схема рекламационной работы"""

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

    # Акт исследования
    research_document: str | None = None
    research_status_id: int | None = None
    investigation_reason_id: int | None = None


class WarrantyWorkUpdate(WarrantyWorkBase):
    """Схема для редактирования рекламационной работы"""

    def validate_dates(self, fault_date=None, existing=None, *, validate_existing=False) -> None:
        """Проверяет изменяемые даты и их связь с датой неисправности"""
        changed = self.model_dump(exclude_unset=True)
        for field in ("notification_date", "re_notification_date", "response_letter_date", "claim_act_date", "work_completion_act_date"):
            if not validate_existing and field not in changed:
                continue
            value = changed[field] if field in changed else getattr(existing, field, None)
            if value is None:
                continue
            if value.year < 2000 or value > date.today():
                raise CaseValidationError(field, "Дата документа должна быть с 2000 года и не позже сегодняшней")
            if fault_date is not None and value < fault_date:
                raise CaseValidationError(field, "Дата рекламационного документа не может быть раньше даты неисправности")


class WarrantyWorkResponse(WarrantyWorkBase):
    """Схема для отображения рекламационной работы"""

    id: int
    case_id: int

    notification_summary: AuxiliaryItem | None = None
    response_summary: AuxiliaryItem | None = None
    decision_summary: AuxiliaryItem | None = None

    research_status: AuxiliaryItem | None = None
    investigation_reason: AuxiliaryItem | None = None

    model_config = ConfigDict(from_attributes=True)
