"""Константы для фильтрации случаев"""

from myapp.models import (
    RepairCaseEquipment,
    WarrantyWork,
    RegionalCenter,
    LocomotiveModel,
    Supplier,
    EquipmentOwner,
    RepairPerformer,
    DestinationType,
    FaultDiscoveryPlace,
    RepairType,
    Equipment,
    Malfunction,
    NotificationSummary,
    ResponseSummary,
    DecisionSummary,
    ResearchStatus,
    InvestigationReason,
    WaybillDoc,
    ShippingProvider,
)

# Битовая маска секции
SECTION_MASKS = [
    {"bit": 1, "name": "А"},
    {"bit": 2, "name": "Б"},
    {"bit": 4, "name": "Бустер"},
]

# Ограничение на количество одновременных запросов к БД
DB_SEMAPHORE_LIMIT = 20

# Конфигурация задач для получения опций фильтров
FILTER_TASK_CONFIGS = [
    # Номера локомотивов и серийные номера
    {
        "name": "locomotive_numbers",
        "func": "FilterOptionsService._get_distinct_values_repair_with_warranty",
        "args": [RepairCaseEquipment.locomotive_number],
    },
    {
        "name": "component_serial_numbers",
        "func": "FilterOptionsService._get_distinct_values_repair_with_warranty",
        "args": [RepairCaseEquipment.component_serial_number_old],
    },
    {
        "name": "element_serial_numbers",
        "func": "FilterOptionsService._get_distinct_values_repair_with_warranty",
        "args": [RepairCaseEquipment.element_serial_number_old],
    },
    {
        "name": "component_serial_numbers_new",
        "func": "FilterOptionsService._get_distinct_values_repair_with_warranty",
        "args": [RepairCaseEquipment.component_serial_number_new],
    },
    {
        "name": "element_serial_numbers_new",
        "func": "FilterOptionsService._get_distinct_values_repair_with_warranty",
        "args": [RepairCaseEquipment.element_serial_number_new],
    },
    # Справочники с JOIN через warranty
    {
        "name": "regional_centers",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            RegionalCenter,
            RepairCaseEquipment.regional_center_id,
            RegionalCenter.regional_center_name,
        ],
    },
    {
        "name": "locomotive_models",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            LocomotiveModel,
            RepairCaseEquipment.locomotive_model_id,
            LocomotiveModel.locomotive_model_name,
        ],
    },
    {
        "name": "suppliers",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            Supplier,
            RepairCaseEquipment.supplier_id,
            Supplier.supplier_name,
        ],
    },
    {
        "name": "equipment_owners",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            EquipmentOwner,
            RepairCaseEquipment.equipment_owner_id,
            EquipmentOwner.equipment_owners_name,
        ],
    },
    {
        "name": "performed_by",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            RepairPerformer,
            RepairCaseEquipment.performed_by_id,
            RepairPerformer.repair_performers_name,
        ],
    },
    {
        "name": "destinations",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            DestinationType,
            RepairCaseEquipment.destination_id,
            DestinationType.destination_types_name,
        ],
    },
    {
        "name": "fault_discovered_at",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            FaultDiscoveryPlace,
            RepairCaseEquipment.fault_discovered_at_id,
            FaultDiscoveryPlace.fault_discovery_places_name,
        ],
    },
    {
        "name": "repair_types",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            RepairType,
            RepairCaseEquipment.repair_type_id,
            RepairType.repair_types_name,
        ],
    },
    # Оборудование и неисправности
    {
        "name": "components",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            Equipment,
            RepairCaseEquipment.component_equipment_id,
            Equipment.equipment_name,
        ],
    },
    {
        "name": "elements",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            Equipment,
            RepairCaseEquipment.element_equipment_id,
            Equipment.equipment_name,
        ],
    },
    {
        "name": "malfunctions",
        "func": "FilterOptionsService._get_used_items_with_warranty_join",
        "args": [
            Malfunction,
            RepairCaseEquipment.malfunction_id,
            Malfunction.defect_name,
        ],
    },
    # Даты и номера уведомлений (из WarrantyWork)
    {
        "name": "notification_numbers",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.notification_number],
    },
    {
        "name": "notification_dates",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.notification_date],
    },
    {
        "name": "re_notification_dates",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.re_notification_date],
    },
    {
        "name": "re_notification_numbers",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.re_notification_number],
    },
    {
        "name": "response_letter_dates",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.response_letter_date],
    },
    {
        "name": "claim_act_dates",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.claim_act_date],
    },
    {
        "name": "work_completion_act_dates",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.work_completion_act_date],
    },
    {
        "name": "response_letter_numbers",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.response_letter_number],
    },
    {
        "name": "claim_act_numbers",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.claim_act_number],
    },
    {
        "name": "work_completion_act_numbers",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.work_completion_act_number],
    },
    # Summaries для рекламационной работы
    {
        "name": "notification_summaries",
        "func": "FilterOptionsService._get_used_items_from_warranty",
        "args": [
            NotificationSummary,
            WarrantyWork.notification_summary_id,
            NotificationSummary.notification_summary_name,
        ],
    },
    {
        "name": "response_summaries",
        "func": "FilterOptionsService._get_used_items_from_warranty",
        "args": [
            ResponseSummary,
            WarrantyWork.response_summary_id,
            ResponseSummary.response_summary_name,
        ],
    },
    {
        "name": "decision_summaries",
        "func": "FilterOptionsService._get_used_items_from_warranty",
        "args": [
            DecisionSummary,
            WarrantyWork.decision_summary_id,
            DecisionSummary.decision_summary_name,
        ],
    },
    # Акт исследования
    {
        "name": "research_statuses",
        "func": "FilterOptionsService._get_used_items_from_warranty",
        "args": [
            ResearchStatus,
            WarrantyWork.research_status_id,
            ResearchStatus.status_name,
        ],
    },
    {
        "name": "investigation_reasons",
        "func": "FilterOptionsService._get_used_items_from_warranty",
        "args": [
            InvestigationReason,
            WarrantyWork.investigation_reason_id,
            InvestigationReason.reason_name,
        ],
    },
    {
        "name": "research_documents",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WarrantyWork.research_document],
    },
    {
        "name": "shipping_providers",
        "func": "FilterOptionsService._get_used_items_from_waybill",
        "args": [
            ShippingProvider,
            WaybillDoc.to_supplier_provider_id,
            ShippingProvider.name_provider,
        ],
    },
    {
        "name": "ttn_replacement",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WaybillDoc.ttn_replacement],
    },
    {
        "name": "ttn_from_rc",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WaybillDoc.ttn_from_rc],
    },
    {
        "name": "ttn_to_supplier",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WaybillDoc.ttn_to_supplier],
    },
    {
        "name": "ttn_from_supplier",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WaybillDoc.ttn_from_supplier],
    },
    {
        "name": "ttn_replacement_dates",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WaybillDoc.ttn_replacement_date],
    },
    {
        "name": "ttn_from_rc_dates",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WaybillDoc.ttn_from_rc_date],
    },
    {
        "name": "ttn_to_supplier_dates",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WaybillDoc.ttn_to_supplier_date],
    },
    {
        "name": "ttn_from_supplier_dates",
        "func": "FilterOptionsService._get_distinct_values_separate_session",
        "args": [WaybillDoc.ttn_from_supplier_date],
    },
]
