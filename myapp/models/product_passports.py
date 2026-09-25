from datetime import date, datetime
from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myapp.database.base import Base


class ProductPassport(Base):
    """Паспорт изделия, импортированный из Omega"""

    __tablename__ = "product_passports"
    __table_args__ = (
        UniqueConstraint("locomotive_model_id", "product_number"),
        Index("ix_product_passports_locomotive_model_id", "locomotive_model_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    locomotive_model_id: Mapped[int] = mapped_column(
        ForeignKey("locomotive_models.id"), nullable=False
    )
    product_number: Mapped[str] = mapped_column(String(50), nullable=False)
    import_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=2, server_default="2"
    )
    omega_root_code: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True
    )
    omega_name: Mapped[str] = mapped_column(Text, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    nodes: Mapped[list["ProductPassportNode"]] = relationship(
        back_populates="passport",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    locomotive_model: Mapped["LocomotiveModel"] = relationship(
        back_populates="product_passports"
    )

    @property
    def locomotive_model_name(self) -> str:
        """Возвращает название связанной модели локомотива"""
        return self.locomotive_model.locomotive_model_name


class ProductPassportNode(Base):
    """Узел дерева паспорта: секция, вагон или оборудование"""

    __tablename__ = "product_passport_nodes"
    __table_args__ = (
        UniqueConstraint("passport_id", "omega_code"),
        Index("ix_product_passport_nodes_passport_id", "passport_id"),
        Index("ix_product_passport_nodes_parent", "passport_id", "parent_omega_code"),
        Index("ix_product_passport_nodes_peshka", "peshka"),
        Index("ix_product_passport_nodes_serial_number", "serial_number"),
        Index("ix_product_passport_nodes_stockobj_code", "stockobj_code"),
        Index("ix_product_passport_nodes_supplier_id", "supplier_id"),
        Index("ix_product_passport_nodes_equipment_id", "equipment_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    passport_id: Mapped[int] = mapped_column(
        ForeignKey("product_passports.id", ondelete="CASCADE"), nullable=False
    )
    omega_code: Mapped[int] = mapped_column(BigInteger, nullable=False)
    parent_omega_code: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    tree_name: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    peshka: Mapped[str | None] = mapped_column(String(50), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manufacture_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    install_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(Text, nullable=True)
    omega_supplier_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id"), nullable=True
    )
    equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipment.id"), nullable=True
    )
    stockobj_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    passport: Mapped["ProductPassport"] = relationship(back_populates="nodes")
    supplier_record: Mapped["Supplier | None"] = relationship()
    equipment_record: Mapped["Equipment | None"] = relationship()
