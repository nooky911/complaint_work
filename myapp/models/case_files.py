from sqlalchemy import Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from enum import Enum as PyEnum

from myapp.database.base import Base


# Первичка или рекл.
class FileCategory(str, PyEnum):
    primary = "primary"
    warranty = "warranty"


# Тип документа для рекл. работы
class WarrantyDocumentField(str, PyEnum):
    notification = "notification"
    re_notification = "re_notification"
    claim_act = "claim_act"
    response = "response"


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
    related_field: Mapped[WarrantyDocumentField | None] = mapped_column(
        Enum(
            WarrantyDocumentField,
            name="warranty_document_field",
            native_enum=True,
        ),
        nullable=True,
    )
    category: Mapped[FileCategory] = mapped_column(
        Enum(
            FileCategory,
            name="file_category",
            native_enum=True,
        ),
        nullable=False,
    )

    # Ключи
    case_id: Mapped[int] = mapped_column(
        ForeignKey("repair_case_equipment.id"), nullable=False
    )

    # Отношения для случая
    case: Mapped["RepairCaseEquipment"] = relationship(
        "RepairCaseEquipment", back_populates="files"
    )
