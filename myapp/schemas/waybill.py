from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date

from myapp.services import CaseValidationError
from .references import AuxiliaryItem


class WaybillDocBase(BaseModel):
    """Базовая схема для ТТН"""

    ttn_replacement: str | None = None
    ttn_replacement_date: date | None = None
    ttn_from_rc: str | None = None
    ttn_from_rc_date: date | None = None
    ttn_to_supplier: str | None = None
    ttn_to_supplier_date: date | None = None
    to_supplier_provider_id: int | None = None
    ttn_from_supplier: str | None = None
    ttn_from_supplier_date: date | None = None
    from_supplier_provider_id: int | None = None

    @field_validator('from_supplier_provider_id')
    @classmethod
    def validate_from_supplier_provider_id(cls, v):
        if v is not None and v > 5:
            raise ValueError('from_supplier_provider_id должен быть в диапазоне 1-5')
        return v


class WaybillDocUpdate(WaybillDocBase):
    """Схема для обновления данных о ТТН"""

    def validate_dates(self) -> None:
        """Проверяет даты ТТН, сохраняя возможность указывать будущую дату"""
        for field in ("ttn_replacement_date", "ttn_from_rc_date", "ttn_to_supplier_date", "ttn_from_supplier_date"):
            value = getattr(self, field)
            if value is not None and value.year < 2000:
                raise CaseValidationError(field, "Дата ТТН должна быть с 2000 года")


class WaybillDocResponse(WaybillDocBase):
    """Схема для отображения ТТН"""

    id: int
    case_id: int

    to_supplier_provider: AuxiliaryItem | None = None
    from_supplier_provider: AuxiliaryItem | None = None

    model_config = ConfigDict(from_attributes=True)
