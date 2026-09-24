from datetime import date
from pydantic import BaseModel


class OmegaPassportNodeData(BaseModel):
    """Данные одного узла паспорта, полученные из Omega"""

    omega_code: int
    parent_omega_code: int | None
    level: int
    tree_name: str
    full_name: str | None
    peshka: str | None
    designation: str | None
    serial_number: str | None
    manufacture_date: date | None
    install_date: date | None
    manufacturer: str | None
    supplier: str | None
    stockobj_code: int | None


class OmegaPassportData(BaseModel):
    """Данные полного паспорта, полученные из Omega"""

    omega_root_code: int
    omega_name: str
    nodes: list[OmegaPassportNodeData]


class OmegaPassportRootData(BaseModel):
    """Корневой паспорт, найденный в Omega"""

    omega_root_code: int
    omega_name: str
