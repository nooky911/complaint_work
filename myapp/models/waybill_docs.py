from sqlalchemy import Integer, Date, String, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date

from myapp.database.base import Base


class WaybillDoc(Base):
    """ТТН о передвижении оборудования"""

    __tablename__ = "waybill_docs"

    __table_args__ = (
        Index("idx_waybill_docs_case_id", "case_id"),
        Index("idx_waybill_ttn_replacement", "ttn_replacement"),
        Index("idx_waybill_ttn_from_rc", "ttn_from_rc"),
        Index("idx_waybill_ttn_to_supplier", "ttn_to_supplier"),
        Index("idx_waybill_ttn_from_supplier", "ttn_from_supplier"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ttn_replacement: Mapped[str | None] = mapped_column(String(50))
    ttn_replacement_date: Mapped[date | None] = mapped_column(Date)

    ttn_from_rc: Mapped[str | None] = mapped_column(String(50))
    ttn_from_rc_date: Mapped[date | None] = mapped_column(Date)

    ttn_to_supplier: Mapped[str | None] = mapped_column(String(50))
    ttn_to_supplier_date: Mapped[date | None] = mapped_column(Date)
    to_supplier_provider_id: Mapped[int | None] = mapped_column(
        ForeignKey("shipping_providers.id")
    )

    ttn_from_supplier: Mapped[str | None] = mapped_column(String(50))
    ttn_from_supplier_date: Mapped[date | None] = mapped_column(Date)
    from_supplier_provider_id: Mapped[int | None] = mapped_column(
        ForeignKey("shipping_providers.id")
    )

    case_id: Mapped[int] = mapped_column(
        ForeignKey("repair_case_equipment.id"), nullable=False, unique=True
    )

    case: Mapped["RepairCaseEquipment"] = relationship(
        "RepairCaseEquipment", back_populates="waybill_doc", uselist=False
    )
    to_supplier_provider: Mapped["ShippingProvider | None"] = relationship(
        "ShippingProvider", foreign_keys=[to_supplier_provider_id]
    )
    from_supplier_provider: Mapped["ShippingProvider | None"] = relationship(
        "ShippingProvider", foreign_keys=[from_supplier_provider_id]
    )


class ShippingProvider(Base):
    """Кто перевозчик?"""

    __tablename__ = "shipping_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_provider: Mapped[str] = mapped_column(String(50), nullable=False)

    @property
    def name(self) -> str:
        """Для корректного использования name в AuxiliaryItem"""
        return self.name_provider
