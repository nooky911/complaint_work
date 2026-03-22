from sqlalchemy import Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from enum import Enum as PyEnum

from myapp.database.base import Base


# Первичка или рекл.
class FileCategory(str, PyEnum):
    primary = "primary"
    warranty = "warranty"
    waybill = "waybill"


# Тип документа для рекл. работы
class WarrantyDocumentField(str, PyEnum):
    notification = "notification"
    re_notification = "re_notification"
    claim_act = "claim_act"
    response = "response"
    research_document = "research_document"


# Тип документа для ТТН
class WaybillDocumentField(str, PyEnum):
    ttn_replacement = "ttn_replacement"
    ttn_from_rc = "ttn_from_rc"
    ttn_to_supplier = "ttn_to_supplier"
    ttn_from_supplier = "ttn_from_supplier"


# Таблица с файлами для первичной и рекламационной документации
class CaseFile(Base):
    __tablename__ = "case_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    related_field: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Enum
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
