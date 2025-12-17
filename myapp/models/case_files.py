from sqlalchemy import Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from enum import Enum as PyEnum

from myapp.database.base import Base


# Первичка или рекл.
class FileCategory(PyEnum):
    PRIMARY = "primary"
    WARRANTY = "warranty"


# Тип документа для рекл. работы
class WarrantyDocumentField(PyEnum):
    NOTIFICATION = "notification"
    RE_NOTIFICATION = "re_notification"
    CLAIM_ACT = "claim_act"
    RESPONSE = "response"


# Таблица с файлами для первичной и рекламационной документации
class CaseFile(Base):
    __tablename__ = "case_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Enum поля
    category: Mapped[FileCategory] = mapped_column(Enum(FileCategory), nullable=False)
    related_field: Mapped[WarrantyDocumentField | None] = mapped_column(
        Enum(WarrantyDocumentField)
    )

    # Ключи
    case_id: Mapped[int] = mapped_column(
        ForeignKey("repair_case_equipment.id"), nullable=False
    )

    # Отношения для случая
    case: Mapped["RepairCaseEquipment"] = relationship(
        "RepairCaseEquipment", back_populates="files"
    )
