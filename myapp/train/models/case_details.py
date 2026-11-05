from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from myapp.database.base import Base


class TrainCaseDetails(Base):
    """Модель, вагоны и поездное оборудование общей записи случая"""

    __tablename__ = "train_case_details"
    case_id: Mapped[int] = mapped_column(
        ForeignKey("repair_case_equipment.id", ondelete="CASCADE"), primary_key=True
    )
    train_model_id: Mapped[int] = mapped_column(ForeignKey("train_models.id"))
    train_number: Mapped[str] = mapped_column(String(50))
    wagon_node_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("train_equipment.id"))
    component_id: Mapped[int | None] = mapped_column(ForeignKey("train_equipment.id"))
    element_id: Mapped[int | None] = mapped_column(ForeignKey("train_equipment.id"))
    new_equipment_id: Mapped[int | None] = mapped_column(
        ForeignKey("train_equipment.id")
    )
    new_component_id: Mapped[int | None] = mapped_column(
        ForeignKey("train_equipment.id")
    )
    new_element_id: Mapped[int | None] = mapped_column(ForeignKey("train_equipment.id"))
    passport_node_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
