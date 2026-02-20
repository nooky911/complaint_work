from sqlalchemy.sql import expression
from sqlalchemy import func

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.schemas.filters import CaseFilterParams

# SQL-выражение для статуса (остается без изменений)
status_expr = func.calculate_case_status(
    WarrantyWork.notification_summary_id,
    WarrantyWork.response_summary_id,
    WarrantyWork.decision_summary_id,
    WarrantyWork.work_completion_act_number,
    WarrantyWork.claim_act_number,
    WarrantyWork.re_notification_number,
    WarrantyWork.re_notification_date,
    WarrantyWork.notification_date,
).label("calculated_status")


def build_repair_case_conditions(
    params: CaseFilterParams,
) -> list[expression.ColumnElement]:
    conditions = []

    # Даты отказа
    if params.date_from:
        conditions.append(RepairCaseEquipment.fault_date >= params.date_from)
    if params.date_to:
        conditions.append(RepairCaseEquipment.fault_date <= params.date_to)

    # Маппинг ID полей
    id_fields = [
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
    ]

    # Маппинг строковых полей и масок
    str_fields = [
        (params.section_mask, RepairCaseEquipment.section_mask),
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

    for p_val, col in id_fields + str_fields:
        if p_val is not None and p_val != "" and p_val != []:
            if isinstance(p_val, list):
                if len(p_val) > 0:
                    conditions.append(col.in_(p_val))
            else:
                conditions.append(col == p_val)

    return conditions


def build_warranty_work_conditions(
    params: CaseFilterParams,
) -> list[expression.ColumnElement]:
    conditions = []

    # Номера документов
    doc_nums = [
        (params.notification_number, WarrantyWork.notification_number),
        (params.re_notification_number, WarrantyWork.re_notification_number),
        (params.response_letter_number, WarrantyWork.response_letter_number),
        (params.claim_act_number, WarrantyWork.claim_act_number),
        (params.work_completion_act_number, WarrantyWork.work_completion_act_number),
    ]

    # Даты документов
    doc_dates = [
        (params.notification_date, WarrantyWork.notification_date),
        (params.re_notification_date, WarrantyWork.re_notification_date),
        (params.response_letter_date, WarrantyWork.response_letter_date),
        (params.claim_act_date, WarrantyWork.claim_act_date),
        (params.work_completion_act_date, WarrantyWork.work_completion_act_date),
    ]

    # Содержания (Summaries)
    summaries = [
        (params.notification_summary_id, WarrantyWork.notification_summary_id),
        (params.response_summary_id, WarrantyWork.response_summary_id),
        (params.decision_summary_id, WarrantyWork.decision_summary_id),
    ]

    for p_val, col in doc_nums + doc_dates + summaries:
        if p_val:
            conditions.append(col.in_(p_val))

    return conditions
