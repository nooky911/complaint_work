from .cases import CaseCreate, CaseUpdate, CaseList, CaseDetail
from .warranty import WarrantyWorkUpdate, WarrantyWorkResponse
from .filters import FilterOptionsResponse, CaseFilterParams
from .references import AuxiliaryItem

__all__ = [
    # Схемы для случаев
    "CaseCreate",
    "CaseUpdate",
    "CaseList",
    "CaseDetail",
    # Схемы для Рекламационной работы
    "WarrantyWorkUpdate",
    "WarrantyWorkResponse",
    # Схемы для Фильтров
    "FilterOptionsResponse",
    "CaseFilterParams",
    # Базовая схема для таблиц формата id, name
    "AuxiliaryItem",
]
