from pydantic import BaseModel, ConfigDict


class EquipmentMalfunctionLink(BaseModel):
    """Схема для связи оборудования и неисправности"""

    equipment_id: int
    malfunction_id: int


class AuxiliaryItem(BaseModel):
    """Базовая схема для справочников, встраиваемых в Caselist/CaseDetail"""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class RepairTypeItem(AuxiliaryItem):
    """Схема для типа ремонта с auto_fill_strategy"""

    auto_fill_strategy: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CaseFormReferencesResponse(BaseModel):
    """Все справочники для формы создания/редактирования случая"""

    regional_centers: list[AuxiliaryItem]
    locomotive_models: list[AuxiliaryItem]
    fault_discovered_at: list[AuxiliaryItem]
    repair_types: list[RepairTypeItem]
    equipment_owners: list[AuxiliaryItem]
    performed_by: list[AuxiliaryItem]
    destinations: list[AuxiliaryItem]
    malfunctions: list[AuxiliaryItem]
    suppliers: list[AuxiliaryItem]
    notification_summaries: list[AuxiliaryItem]
    response_summaries: list[AuxiliaryItem]
    decision_summaries: list[AuxiliaryItem]
    equipment_malfunctions: list[EquipmentMalfunctionLink]
