from sqlalchemy import Integer, String, Date, Text, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import date, datetime

from database.base import Base


# Основная таблица со случаями неисправности
class RepairCaseEquipment(Base):
    __tablename__ = "repair_case_equipment"

    # Основные поля
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date_recorded: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    fault_date: Mapped[date] = mapped_column(Date, nullable=False)
    section_mask: Mapped[int] = mapped_column(Integer, nullable=False)
    locomotive_number: Mapped[str | None] = mapped_column(String(50))
    mileage: Mapped[int | None] = mapped_column(Integer)
    component_quantity: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    element_quantity: Mapped[int | None] = mapped_column(Integer)
    component_serial_number_old: Mapped[str | None] = mapped_column(String(100))
    component_manufacture_date_old: Mapped[date | None] = mapped_column(Date)
    element_serial_number_old: Mapped[str | None] = mapped_column(String(100))
    element_manufacture_date_old: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    component_serial_number_new: Mapped[str | None] = mapped_column(String(100))
    component_manufacture_date_new: Mapped[date | None] = mapped_column(Date)
    element_serial_number_new: Mapped[str | None] = mapped_column(String(100))
    element_manufacture_date_new: Mapped[date | None] = mapped_column(Date)

    # Внешние ключи
    regional_center_id: Mapped[int] = mapped_column(ForeignKey("regional_centers.id"), nullable=False)
    locomotive_model_id: Mapped[int] = mapped_column(ForeignKey("locomotive_models.id"), nullable=False)
    fault_discovered_at_id: Mapped[int] = mapped_column(ForeignKey("fault_discovery_places.id"), nullable=False)
    component_equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False)
    element_equipment_id: Mapped[int | None] = mapped_column(ForeignKey("equipment.id"))
    malfunction_id: Mapped[int] = mapped_column(ForeignKey("malfunctions.id"), nullable=False)
    repair_type_id: Mapped[int] = mapped_column(ForeignKey("repair_types.id"), nullable=False)
    performed_by_id: Mapped[int | None] = mapped_column(ForeignKey("repair_performers.id"))
    equipment_owner_id: Mapped[int | None] = mapped_column(ForeignKey("equipment_owners.id"))
    destination_id: Mapped[int | None] = mapped_column(ForeignKey("destination_types.id"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))

    # Отношения
    regional_center: Mapped["RegionalCenter"] = relationship("RegionalCenter", back_populates="repair_cases")
    locomotive_model: Mapped["LocomotiveModel"] = relationship("LocomotiveModel", back_populates="repair_cases")
    fault_discovered_at: Mapped["FaultDiscoveryPlace"] = relationship(
        "FaultDiscoveryPlace",
        back_populates="repair_cases"
    )
    component_equipment: Mapped["Equipment"] = relationship(
        "Equipment",
        foreign_keys=[component_equipment_id],
        back_populates="component_repair_cases"
    )
    element_equipment: Mapped["Equipment | None"] = relationship(
        "Equipment",
        foreign_keys=[element_equipment_id],
        back_populates="element_repair_cases"
    )
    malfunction: Mapped["Malfunction"] = relationship("Malfunction", back_populates="repair_cases")
    repair_type: Mapped["RepairType"] = relationship("RepairType", back_populates="repair_cases")
    performed_by: Mapped["RepairPerformer | None"] = relationship(
        "RepairPerformer",
        back_populates="repair_cases"
    )
    equipment_owner: Mapped["EquipmentOwner | None"] = relationship(
        "EquipmentOwner",
        back_populates="repair_cases"
    )
    destination: Mapped["DestinationType | None"] = relationship(
        "DestinationType",
        back_populates="repair_cases"
    )
    supplier: Mapped["Supplier | None"] = relationship("Supplier", back_populates="repair_cases")
    warranty_work: Mapped["WarrantyWork"] = relationship(
        "WarrantyWork",
        back_populates="case",
        uselist=False,
        cascade="all, delete-orphan"
    )