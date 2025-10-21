from pydantic import BaseModel
from typing import List

class FilterOption(BaseModel):
    id: int
    name: str

class FilterOptionsResponse(BaseModel):
    regional_centers: List[FilterOption]
    locomotive_models: List[FilterOption]
    components: List[FilterOption]
    malfunctions: List[FilterOption]
    suppliers: List[FilterOption]
    repair_types: List[FilterOption]
    statuses: List[str]