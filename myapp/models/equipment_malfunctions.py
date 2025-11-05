from sqlalchemy import Text, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from myapp.database.base import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    equipment_name: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("equipment.id"))
    type: Mapped[str | None] = mapped_column(Text)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))

    # Отношения
    parent: Mapped["Equipment | None"] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Equipment"]] = relationship(back_populates="parent")
    supplier: Mapped["Supplier | None"] = relationship(back_populates="equipment")
    component_repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        foreign_keys="[RepairCaseEquipment.component_equipment_id]",
        back_populates="component_equipment",
    )
    element_repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        foreign_keys="[RepairCaseEquipment.element_equipment_id]",
        back_populates="element_equipment",
    )
    malfunctions: Mapped[list["Malfunction"]] = relationship(
        secondary="equipment_malfunctions", back_populates="equipment"
    )

    @property
    def name(self) -> str:
        """Для корректного использования name в AuxiliaryItem"""
        return self.equipment_name


class Malfunction(Base):
    """Виды неисправностей"""

    __tablename__ = "malfunctions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    defect_name: Mapped[str] = mapped_column(Text)

    repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment", back_populates="malfunction"
    )
    equipment: Mapped[list["Equipment"]] = relationship(
        secondary="equipment_malfunctions", back_populates="malfunctions"
    )

    @property
    def name(self) -> str:
        """Для корректного использования name в AuxiliaryItem"""
        return self.defect_name


class EquipmentMalfunction(Base):
    """
    Таблица связи (association table) для связи «Оборудование <-> Неисправности».
    Каждая строка связывает одно оборудование с одной неисправностью, которую оно может иметь.
    Таблица не имеет собственного id, только внешние ключи
    """

    __tablename__ = "equipment_malfunctions"
    __table_args__ = (PrimaryKeyConstraint("equipment_id", "malfunction_id"),)

    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id"), nullable=False
    )
    malfunction_id: Mapped[int] = mapped_column(
        ForeignKey("malfunctions.id"), nullable=False
    )
