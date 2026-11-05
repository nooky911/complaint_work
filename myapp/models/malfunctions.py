from sqlalchemy import Text, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from myapp.database.base import Base


class Malfunction(Base):
    """Виды неисправностей"""

    __tablename__ = "malfunctions"

    __table_args__ = (Index("idx_malfunction_defect_name", "defect_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    defect_name: Mapped[str] = mapped_column(Text)

    repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment", back_populates="malfunction"
    )
    equipment: Mapped[list["Equipment"]] = relationship(
        secondary="loco_equipment_malfunctions", back_populates="malfunctions"
    )

    @property
    def name(self) -> str:
        """Для корректного использования name в AuxiliaryItem"""
        return self.defect_name
