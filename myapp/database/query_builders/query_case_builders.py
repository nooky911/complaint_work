from sqlalchemy.orm import joinedload

from myapp.models.equipment_malfunctions import Equipment
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork


def load_list_relations():
    """Связи для отображения в списке фильтрации"""
    return [
        joinedload(RepairCaseEquipment.regional_center),
        joinedload(RepairCaseEquipment.locomotive_model),
        joinedload(RepairCaseEquipment.component_equipment).joinedload(
            Equipment.parent
        ),
        joinedload(RepairCaseEquipment.element_equipment).joinedload(Equipment.parent),
        joinedload(RepairCaseEquipment.malfunction),
        joinedload(RepairCaseEquipment.repair_type),
        joinedload(RepairCaseEquipment.supplier),
        joinedload(RepairCaseEquipment.user),
        joinedload(RepairCaseEquipment.warranty_work).joinedload(
            WarrantyWork.notification_summary
        ),
        joinedload(RepairCaseEquipment.warranty_work).joinedload(
            WarrantyWork.response_summary
        ),
        joinedload(RepairCaseEquipment.warranty_work).joinedload(
            WarrantyWork.decision_summary
        ),
    ]


def load_detail_relations():
    """Полный набор связей для детального просмотра"""
    relations = load_list_relations()

    relations.extend(
        [
            joinedload(RepairCaseEquipment.fault_discovered_at),
            joinedload(RepairCaseEquipment.performed_by),
            joinedload(RepairCaseEquipment.equipment_owner),
            joinedload(RepairCaseEquipment.destination),
        ]
    )
    return relations
