from datetime import date, datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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
    commissioned_at: Mapped[date | None] = mapped_column(Date, nullable=True)
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
    # Сохраняем имя существующей колонки для совместимости с импортированными данными.
    article: Mapped[str | None] = mapped_column("peshka", String(50), nullable=True)
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

    baseline_state: Mapped[dict | None] = mapped_column(JSONB)
    baseline_source: Mapped[str | None] = mapped_column(String(30))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    is_present: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    manufacture_date_text: Mapped[str | None] = mapped_column(String(100))

    passport: Mapped["ProductPassport"] = relationship(back_populates="nodes")
    supplier_record: Mapped["Supplier | None"] = relationship()
    equipment_record: Mapped["Equipment | None"] = relationship()


class ProductPassportEquipmentMatch(Base):
    """Подтверждённое соответствие позиции Omega оборудованию справочника"""

    __tablename__ = "product_passport_equipment_matches"

    match_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    omega_tree_name: Mapped[str] = mapped_column(Text, nullable=False)
    omega_designation: Mapped[str | None] = mapped_column(Text, nullable=True)
    omega_supplier_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    omega_manufacturer: Mapped[str | None] = mapped_column(Text, nullable=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id"), nullable=False
    )
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id"), nullable=True
    )


class ProductPassportEquipmentSerialMatch(Base):
    """Подтверждённое соответствие с учётом длины заводского номера"""

    __tablename__ = "product_passport_equipment_serial_matches"

    match_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    serial_length: Mapped[int] = mapped_column(Integer, primary_key=True)
    omega_tree_name: Mapped[str] = mapped_column(Text, nullable=False)
    omega_designation: Mapped[str | None] = mapped_column(Text, nullable=True)
    omega_supplier_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    omega_manufacturer: Mapped[str | None] = mapped_column(Text, nullable=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id"), nullable=False
    )
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id"), nullable=True
    )


class CasePassportLink(Base):
    """Выбранный неисправный экземпляр внутри уже связанного паспорта"""

    __tablename__ = "case_passport_links"
    __table_args__ = (
        UniqueConstraint("case_id", "node_id", "role"),
        UniqueConstraint("case_id", "id"),
        CheckConstraint("role IN ('component', 'element')"),
        ForeignKeyConstraint(
            ["case_id", "parent_link_id"],
            ["case_passport_links.case_id", "case_passport_links.id"],
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("repair_case_equipment.id", ondelete="CASCADE"), index=True
    )
    node_id: Mapped[int] = mapped_column(
        ForeignKey("product_passport_nodes.id", ondelete="RESTRICT"), index=True
    )
    role: Mapped[str] = mapped_column(String(12))
    parent_link_id: Mapped[int | None] = mapped_column(BigInteger)
    selected_state: Mapped[dict] = mapped_column(JSONB)
    position_context: Mapped[dict] = mapped_column(JSONB)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ProductPassportEvent(Base):
    """Редакция замены или ручного исправления"""

    __tablename__ = "product_passport_events"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('case_replacement', 'manual_correction', 'historical_replacement')"
        ),
        CheckConstraint("status IN ('active', 'superseded', 'voided')"),
        CheckConstraint("kind != 'manual_correction' OR length(trim(reason)) > 0"),
        UniqueConstraint("source_case_id", "revision"),
        Index(
            "ux_passport_active_case_event",
            "case_id",
            unique=True,
            postgresql_where=text("kind='case_replacement' AND status='active'"),
        ),
        Index(
            "ix_passport_events_order",
            "passport_id",
            "effective_date",
            "day_order",
            "id",
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    passport_id: Mapped[int] = mapped_column(
        ForeignKey("product_passports.id", ondelete="RESTRICT")
    )
    case_id: Mapped[int | None] = mapped_column(
        ForeignKey("repair_case_equipment.id", ondelete="SET NULL"), index=True
    )
    source_case_id: Mapped[int | None] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(25))
    case_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    effective_date: Mapped[date] = mapped_column(Date)
    day_order: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    actor_name: Mapped[str] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    supersedes_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_passport_events.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(String(15), default="active")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    closed_by_name: Mapped[str | None] = mapped_column(Text)
    close_reason: Mapped[str | None] = mapped_column(Text)


class ProductPassportEventItem(Base):
    """Изменение конкретной позиции паспорта в записи истории"""

    __tablename__ = "product_passport_event_items"
    __table_args__ = (UniqueConstraint("event_id", "node_id"),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("product_passport_events.id", ondelete="RESTRICT"), index=True
    )
    node_id: Mapped[int] = mapped_column(
        ForeignKey("product_passport_nodes.id", ondelete="RESTRICT"), index=True
    )
    scope: Mapped[str] = mapped_column(String(15))
    group_key: Mapped[str | None] = mapped_column(Text)
    position_context: Mapped[dict] = mapped_column(JSONB)
    before_state: Mapped[dict] = mapped_column(JSONB)
    after_state: Mapped[dict] = mapped_column(JSONB)
    changed_fields: Mapped[list[str]] = mapped_column(ARRAY(Text))


class ProductPassportFile(Base):
    """Пользовательский скан конкретного экземпляра на позиции паспорта"""

    __tablename__ = "product_passport_files"
    __table_args__ = (Index("ix_passport_files_instance", "node_id", "instance_key"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    node_id: Mapped[int] = mapped_column(
        ForeignKey("product_passport_nodes.id", ondelete="RESTRICT"), nullable=False
    )
    instance_key: Mapped[str] = mapped_column(String(80), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    uploaded_by_name: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
