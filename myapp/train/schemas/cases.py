from datetime import date
from pydantic import BaseModel, ConfigDict, Field

from myapp.schemas.cases import CaseBase, PassportLinkInput
from myapp.schemas.warranty import WarrantyWorkUpdate
from myapp.schemas.waybill import WaybillDocUpdate


class TrainDetailsInput(BaseModel):
    """Вагоны и уровни поездного оборудования без локомотивных ID"""

    model_config = ConfigDict(extra="forbid")
    train_model_id: int = Field(gt=0)
    wagon_node_ids: list[int] = Field(min_length=1, max_length=20)
    equipment_id: int = Field(gt=0)
    component_id: int | None = None
    element_id: int | None = None
    new_equipment_id: int | None = None
    new_component_id: int | None = None
    new_element_id: int | None = None
    passport_node_ids: list[int] = Field(default_factory=list, max_length=100)


class TrainCaseInput(CaseBase):
    """Полная форма создания или редактирования поездного случая"""

    model_config = ConfigDict(extra="forbid")
    user_id: int | None = None
    fault_date: date
    passport_id: int = Field(gt=0)
    regional_center_id: int = Field(gt=0)
    fault_discovered_at_id: int = Field(gt=0)
    malfunction_id: int = Field(gt=0)
    repair_type_id: int = Field(gt=0)
    component_quantity: int = Field(default=1, gt=0)
    train: TrainDetailsInput
    warranty_work: WarrantyWorkUpdate = Field(default_factory=WarrantyWorkUpdate)
    waybill_doc: WaybillDocUpdate = Field(default_factory=WaybillDocUpdate)


class TrainReplacementPreview(BaseModel):
    """Параметры расчёта поездной замены в выбранных вагонах"""

    train: TrainDetailsInput
    repair_type_id: int
    fault_date: date | None = None
    case_id: int | None = None
    passport_links: list[PassportLinkInput] | None = None
