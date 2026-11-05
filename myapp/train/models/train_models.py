from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from myapp.database.base import Base


class TrainModel(Base):
    """Модель поезда, количество вагонов определяется деревом конкретного паспорта"""

    __tablename__ = "train_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    train_model_name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    product_passports: Mapped[list["ProductPassport"]] = relationship(
        back_populates="train_model"
    )
