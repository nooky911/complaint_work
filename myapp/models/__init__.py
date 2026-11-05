from .warranty_work import (
    WarrantyWork,
    NotificationSummary,
    ResponseSummary,
    DecisionSummary,
    ResearchStatus,
    InvestigationReason,
)
from myapp.loco.models.equipment import Equipment, EquipmentMalfunction
from myapp.models.malfunctions import Malfunction
from .repair_case_equipment import RepairCaseEquipment
from .case_files import (
    CaseFile,
    FileCategory,
    WarrantyDocumentField,
)
from .auxiliaries import (
    RegionalCenter,
    LocomotiveModel,
    LocomotiveNumberException,
    FaultDiscoveryPlace,
    RepairType,
    RepairPerformer,
    EquipmentOwner,
    DestinationType,
    Supplier,
    OmegaStockSupplierName,
)
from .waybill_docs import WaybillDoc, ShippingProvider
from .product_passports import (
    ProductPassport,
    ProductPassportNode,
    ProductPassportEquipmentMatch,
    ProductPassportEquipmentSerialMatch,
    CasePassportLink,
    ProductPassportEvent,
    ProductPassportEventItem,
    ProductPassportFile,
)
from .user import User, UserEditPartner
from myapp.train.models.train_models import TrainModel
from myapp.train.models.equipment import TrainEquipment, TrainEquipmentMalfunction
from myapp.train.models.case_details import TrainCaseDetails
