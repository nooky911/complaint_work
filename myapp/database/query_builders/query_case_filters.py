from sqlalchemy.sql import expression

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.schemas.filters import CaseFilterParams
from myapp.services.case_status_service import CaseStatusService


def apply_filter_conditions(conditions: list, fields_mapping: list):
    for p_val, col in fields_mapping:
        if p_val is not None:
            if isinstance(p_val, list):
                clean_list = [v for v in p_val if v != "" and v is not None and v != 0]
                if clean_list:
                    conditions.append(col.in_(clean_list))
            else:
                val_str = str(p_val).strip()
                if val_str != "" and p_val != 0:
                    conditions.append(col == p_val)


def build_repair_case_conditions(
    params: CaseFilterParams,
) -> list[expression.ColumnElement]:
    conditions = []

    # 1. Даты
    if params.date_from:
        conditions.append(RepairCaseEquipment.fault_date >= params.date_from)
    if params.date_to:
        conditions.append(RepairCaseEquipment.fault_date <= params.date_to)

    # 2. Маппинг всех полей RepairCase
    repair_fields = [
        (params.regional_center_id, RepairCaseEquipment.regional_center_id),
        (params.locomotive_model_id, RepairCaseEquipment.locomotive_model_id),
        (params.component_equipment_id, RepairCaseEquipment.component_equipment_id),
        (params.element_equipment_id, RepairCaseEquipment.element_equipment_id),
        (params.malfunction_id, RepairCaseEquipment.malfunction_id),
        (params.repair_type_id, RepairCaseEquipment.repair_type_id),
        (params.supplier_id, RepairCaseEquipment.supplier_id),
        (params.equipment_owner_id, RepairCaseEquipment.equipment_owner_id),
        (params.performed_by_id, RepairCaseEquipment.performed_by_id),
        (params.destination_id, RepairCaseEquipment.destination_id),
        (params.user_id, RepairCaseEquipment.user_id),
        (params.locomotive_number, RepairCaseEquipment.locomotive_number),
        (
            params.component_serial_number_old,
            RepairCaseEquipment.component_serial_number_old,
        ),
        (
            params.element_serial_number_old,
            RepairCaseEquipment.element_serial_number_old,
        ),
        (
            params.component_serial_number_new,
            RepairCaseEquipment.component_serial_number_new,
        ),
        (
            params.element_serial_number_new,
            RepairCaseEquipment.element_serial_number_new,
        ),
        (params.notes, RepairCaseEquipment.notes),
    ]

    apply_filter_conditions(conditions, repair_fields)

    # 3. Специфические поля
    if params.section_mask is not None and params.section_mask != 0:
        conditions.append(RepairCaseEquipment.section_mask == params.section_mask)

    if params.status:
        # Убираем пустые значения, если они есть
        clean_statuses = [s for s in params.status if s]
        if clean_statuses:
            status_subquery = CaseStatusService.build_status_subquery()
            conditions.append(status_subquery.in_(clean_statuses))

    return conditions


def build_warranty_work_conditions(
    params: CaseFilterParams,
) -> list[expression.ColumnElement]:
    conditions = []

    warranty_fields = [
        (params.notification_number, WarrantyWork.notification_number),
        (params.re_notification_number, WarrantyWork.re_notification_number),
        (params.response_letter_number, WarrantyWork.response_letter_number),
        (params.claim_act_number, WarrantyWork.claim_act_number),
        (params.work_completion_act_number, WarrantyWork.work_completion_act_number),
        (params.notification_date, WarrantyWork.notification_date),
        (params.re_notification_date, WarrantyWork.re_notification_date),
        (params.response_letter_date, WarrantyWork.response_letter_date),
        (params.claim_act_date, WarrantyWork.claim_act_date),
        (params.work_completion_act_date, WarrantyWork.work_completion_act_date),
        (params.notification_summary_id, WarrantyWork.notification_summary_id),
        (params.response_summary_id, WarrantyWork.response_summary_id),
        (params.decision_summary_id, WarrantyWork.decision_summary_id),
    ]

    apply_filter_conditions(conditions, warranty_fields)

    return conditions
