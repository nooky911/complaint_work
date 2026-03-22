from .cases import CaseCreate, CaseUpdate, CaseList, CaseDetail, SupplierPreviewRequest
from .warranty import WarrantyWorkUpdate, WarrantyWorkResponse
from .filters import FilterOptionsResponse, CaseFilterParams
from .references import AuxiliaryItem
from .waybill import WaybillDocUpdate, WaybillDocResponse

__all__ = [
    # Схемы для случаев
    "CaseCreate",
    "CaseUpdate",
    "CaseList",
    "CaseDetail",
    "SupplierPreviewRequest",
    # Схемы для Рекламационной работы
    "WarrantyWorkUpdate",
    "WarrantyWorkResponse",
    # Схемы для Фильтров
    "FilterOptionsResponse",
    "CaseFilterParams",
    # Базовая схема для таблиц формата id, name
    "AuxiliaryItem",
    # Схемы для ТТН документов
    "WaybillDocUpdate",
    "WaybillDocResponse",
]
