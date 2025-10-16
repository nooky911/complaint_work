from database import Base

from .warranty_work import WarrantyWork
from .equipment_mulfunctions import Equipment, EquipmentMalfunction, Malfunction
from .repair_case_equipment import RepairCaseEquipment
from .auxiliaries import (
    RegionalCenter, LocomotiveModel, FaultDiscoveryPlace, RepairType,
    RepairPerformer, EquipmentOwner, DestinationType, Supplier
)