from sqlalchemy import Text, ForeignKey, PrimaryKeyConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from myapp.database.base import Base


class Equipment(Base):
    __tablename__ = "loco_equipment"

    __table_args__ = (Index("idx_loco_equipment_name", "equipment_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    equipment_name: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("loco_equipment.id"))
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
        secondary="loco_equipment_malfunctions", back_populates="equipment"
    )
    new_component_repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment",
        foreign_keys="[RepairCaseEquipment.new_component_equipment_id]",
        back_populates="new_component_equipment",
    )
    new_element_repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment",
        foreign_keys="[RepairCaseEquipment.new_element_equipment_id]",
        back_populates="new_element_equipment",
    )

    @property
    def name(self) -> str:
        """Для корректного использования name в AuxiliaryItem"""
        return self.equipment_name


class EquipmentMalfunction(Base):
    """
    Таблица связи (association table) для связи «Оборудование <-> Неисправности».
    Каждая строка связывает одно оборудование с одной неисправностью, которую оно может иметь.
    Таблица не имеет собственного id, только внешние ключи
    """

    __tablename__ = "loco_equipment_malfunctions"
    __table_args__ = (PrimaryKeyConstraint("equipment_id", "malfunction_id"),)

    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("loco_equipment.id"), nullable=False
    )
    malfunction_id: Mapped[int] = mapped_column(
        ForeignKey("malfunctions.id"), nullable=False
    )
