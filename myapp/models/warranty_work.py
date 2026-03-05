from sqlalchemy import Integer, String, Date, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date

from myapp.database.base import Base


class WarrantyWork(Base):
    __tablename__ = "warranty_work"

    # Индексы для оптимизации фильтров документации
    __table_args__ = (
        Index("idx_warranty_work_case_id", "case_id"),
        Index("idx_warranty_work_notification_number", "notification_number"),
        Index("idx_warranty_work_re_notification_number", "re_notification_number"),
        Index("idx_warranty_work_response_letter_number", "response_letter_number"),
        Index("idx_warranty_work_claim_act_number", "claim_act_number"),
        Index(
            "idx_warranty_work_work_completion_act_number", "work_completion_act_number"
        ),
        # Даты документации
        Index("idx_warranty_work_notification_date", "notification_date"),
        Index("idx_warranty_work_re_notification_date", "re_notification_date"),
        Index("idx_warranty_work_response_letter_date", "response_letter_date"),
        Index("idx_warranty_work_claim_act_date", "claim_act_date"),
        Index("idx_warranty_work_work_completion_act_date", "work_completion_act_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification_number: Mapped[str | None] = mapped_column(String(50))
    notification_date: Mapped[date | None] = mapped_column(Date)
    re_notification_number: Mapped[str | None] = mapped_column(String(50))
    re_notification_date: Mapped[date | None] = mapped_column(Date)
    response_letter_number: Mapped[str | None] = mapped_column(String(50))
    response_letter_date: Mapped[date | None] = mapped_column(Date)
    claim_act_number: Mapped[str | None] = mapped_column(String(50))
    claim_act_date: Mapped[date | None] = mapped_column(Date)
    work_completion_act_number: Mapped[str | None] = mapped_column(String(50))
    work_completion_act_date: Mapped[date | None] = mapped_column(Date)

    notification_summary_id: Mapped[int | None] = mapped_column(
        ForeignKey("notification_summary.id")
    )
    response_summary_id: Mapped[int | None] = mapped_column(
        ForeignKey("response_summary.id")
    )
    decision_summary_id: Mapped[int | None] = mapped_column(
        ForeignKey("decision_summary.id")
    )
    case_id: Mapped[int] = mapped_column(
        ForeignKey("repair_case_equipment.id"), nullable=False
    )

    notification_summary: Mapped["NotificationSummary | None"] = relationship(
        "NotificationSummary", back_populates="warranty_work"
    )
    response_summary: Mapped["ResponseSummary | None"] = relationship(
        "ResponseSummary", back_populates="warranty_work"
    )
    decision_summary: Mapped["DecisionSummary | None"] = relationship(
        "DecisionSummary", back_populates="warranty_work"
    )
    case: Mapped["RepairCaseEquipment"] = relationship(
        "RepairCaseEquipment", back_populates="warranty_work", uselist=False
    )


class NotificationSummary(Base):
    __tablename__ = "notification_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification_summary_name: Mapped[str] = mapped_column(String(255))

    warranty_work: Mapped[list["WarrantyWork"]] = relationship(
        "WarrantyWork", back_populates="notification_summary"
    )

    @property
    def name(self) -> str:
        """Для корректного использования name в AuxiliaryItem"""
        return self.notification_summary_name


class ResponseSummary(Base):
    __tablename__ = "response_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    response_summary_name: Mapped[str] = mapped_column(String(255))

    warranty_work: Mapped[list["WarrantyWork"]] = relationship(
        "WarrantyWork", back_populates="response_summary"
    )

    @property
    def name(self) -> str:
        """Для корректного использования name в AuxiliaryItem"""
        return self.response_summary_name


class DecisionSummary(Base):
    __tablename__ = "decision_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_summary_name: Mapped[str] = mapped_column(String(255))

    warranty_work: Mapped[list["WarrantyWork"]] = relationship(
        "WarrantyWork", back_populates="decision_summary"
    )

    @property
    def name(self) -> str:
        """Для корректного использования name в AuxiliaryItem"""
        return self.decision_summary_name
