from sqlalchemy import Text, ForeignKey, Integer, Index, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myapp.database.base import Base


class TrainEquipment(Base):
    """Позиция поездного дерева с наследованием поставщика по родителю"""

    __tablename__ = "train_equipment"
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_name: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("train_equipment.id", ondelete="RESTRICT")
    )
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT")
    )
    manufacturer: Mapped[str | None] = mapped_column(Text)
    designation: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        Index(
            "uq_train_equipment_parent_name",
            func.coalesce(parent_id, 0),
            equipment_name,
            unique=True,
        ),
        Index("ix_train_equipment_parent_id", parent_id),
        CheckConstraint("level BETWEEN 1 AND 4"),
        CheckConstraint("parent_id IS NULL OR parent_id <> id"),
    )
    parent: Mapped["TrainEquipment | None"] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list["TrainEquipment"]] = relationship(back_populates="parent")
    supplier: Mapped["Supplier | None"] = relationship()
    malfunctions: Mapped[list["Malfunction"]] = relationship(
        secondary="train_equipment_malfunctions"
    )


class TrainEquipmentMalfunction(Base):
    """Привязка поездного оборудования к существующей или новой неисправности"""

    __tablename__ = "train_equipment_malfunctions"
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("train_equipment.id", ondelete="CASCADE"), primary_key=True
    )
    malfunction_id: Mapped[int] = mapped_column(
        ForeignKey("malfunctions.id", ondelete="RESTRICT"), primary_key=True
    )
