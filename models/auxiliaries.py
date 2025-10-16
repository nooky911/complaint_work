from sqlalchemy import String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base


class RegionalCenter(Base):
    """Региональный центр"""
    __tablename__ = "regional_centers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    regional_center_name: Mapped[str] = mapped_column(String(100))

    repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment",
        back_populates="regional_center"
    )


class LocomotiveModel(Base):
    """Модели локомотивов"""
    __tablename__ = "locomotive_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    locomotive_model_name: Mapped[str] = mapped_column(String(50))

    repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment",
        back_populates="locomotive_model"
    )


class FaultDiscoveryPlace(Base):
    """Где обнаружилась неиспроавнсть?"""
    __tablename__ = "fault_discovery_places"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fault_discovery_places_name: Mapped[str] = mapped_column(String(50))

    repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment",
        back_populates="fault_discovered_at"
    )


class RepairType(Base):
    """Что сделано с неисправным оборудованием?"""
    __tablename__ = "repair_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    repair_types_name: Mapped[str] = mapped_column(String(255))

    repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment",
        back_populates="repair_type"
    )


class RepairPerformer(Base):
    """Кто устранял неисправность?"""
    __tablename__ = "repair_performers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    repair_performers_name: Mapped[str] = mapped_column(String(255))

    repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment",
        back_populates="performed_by"
    )


class EquipmentOwner(Base):
    __tablename__ = "equipment_owners"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    equipment_owners_name: Mapped[str] = mapped_column(String(100))

    repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment",
        back_populates="equipment_owner"
    )


class DestinationType(Base):
    __tablename__ = "destination_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    destination_types_name: Mapped[str] = mapped_column(String(100))

    repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment",
        back_populates="destination")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    supplier_name: Mapped[str] = mapped_column(String(100))

    repair_cases: Mapped[list["RepairCaseEquipment"]] = relationship(
        "RepairCaseEquipment",
        back_populates="supplier")
    equipment: Mapped[list["Equipment"]] = relationship("Equipment", back_populates="supplier")