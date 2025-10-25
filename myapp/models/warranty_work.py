from sqlalchemy import Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date

from myapp.database.base import Base


class WarrantyWork(Base):
    __tablename__ = "warranty_work"

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

    notification_summary_id: Mapped[int | None] = mapped_column(ForeignKey("notification_summary.id"))
    response_summary_id: Mapped[int | None] = mapped_column(ForeignKey("response_summary.id"))
    decision_summary_id: Mapped[int | None] = mapped_column(ForeignKey("decision_summary.id"))
    case_id: Mapped[int] = mapped_column(ForeignKey("repair_case_equipment.id"), nullable=False)

    notification_summary: Mapped["NotificationSummary | None"] = relationship(
        "NotificationSummary",
        back_populates="warranty_work"
    )
    response_summary: Mapped["ResponseSummary | None"] = relationship(
        "ResponseSummary",
        back_populates="warranty_work"
    )
    decision_summary: Mapped["DecisionSummary | None"] = relationship(
        "DecisionSummary",
        back_populates="warranty_work"
    )
    case: Mapped["RepairCaseEquipment"] = relationship(
        "RepairCaseEquipment",
        back_populates="warranty_work",
        uselist=False
    )



class NotificationSummary(Base):
    __tablename__ = "notification_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification_summary_name: Mapped[str] = mapped_column(String(255))

    warranty_work: Mapped[list["WarrantyWork"]] = relationship(
        "WarrantyWork",
        back_populates="notification_summary"
    )


class ResponseSummary(Base):
    __tablename__ = "response_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    response_summary_name: Mapped[str] = mapped_column(String(255))

    warranty_work: Mapped[list["WarrantyWork"]] = relationship(
        "WarrantyWork",
        back_populates="response_summary"
    )


class DecisionSummary(Base):
    __tablename__ = "decision_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_summary_name: Mapped[str] = mapped_column(String(255))

    warranty_work: Mapped[list["WarrantyWork"]] = relationship(
        "WarrantyWork",
        back_populates="decision_summary"
    )
