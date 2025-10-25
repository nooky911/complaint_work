from pydantic import BaseModel, ConfigDict

class AuxiliaryItem(BaseModel):
    """Базовая схема для справочников, встраиваемых в CaseList/CaseDetail"""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)