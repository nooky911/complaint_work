from sqlalchemy.sql import expression
from sqlalchemy import func

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.schemas.filters import CaseFilterParams

# SQL-выражение для статуса
status_expr = func.calculate_case_status(
    WarrantyWork.notification_summary_id,
    WarrantyWork.response_summary_id,
    WarrantyWork.decision_summary_id,
    WarrantyWork.work_completion_act_number,
    WarrantyWork.claim_act_number,
    WarrantyWork.re_notification_number,
    WarrantyWork.re_notification_date,
    WarrantyWork.notification_date
).label('calculated_status')


def build_repair_case_conditions(params: CaseFilterParams) -> list[expression.ColumnElement]:
    """WHERE фильтрация для repair_case_equipment"""
    conditions = []

    # Даты
    if params.date_from:
        conditions.append(RepairCaseEquipment.fault_date >= params.date_from)
    if params.date_to:
        conditions.append(RepairCaseEquipment.fault_date <= params.date_to)

    # Числа/строки
    if params.locomotive_number:
        conditions.append(RepairCaseEquipment.locomotive_number.ilike(f"%{params.locomotive_number}%"))
    if params.component_serial_number_old:
        conditions.append(
            RepairCaseEquipment.component_serial_number_old.ilike(f"%{params.component_serial_number_old}%"))
    if params.element_serial_number_old:
        conditions.append(RepairCaseEquipment.element_serial_number_old.ilike(f"%{params.element_serial_number_old}%"))
    if params.component_serial_number_new:
        conditions.append(
            RepairCaseEquipment.component_serial_number_new.ilike(f"%{params.component_serial_number_new}%"))
    if params.element_serial_number_new:
        conditions.append(RepairCaseEquipment.element_serial_number_new.ilike(f"%{params.element_serial_number_new}%"))

    # Битовая маска для секции
    if params.section_mask is not None:
        conditions.append(RepairCaseEquipment.section_mask == params.section_mask)

    # Для ID
    if params.regional_center_id is not None:
        conditions.append(RepairCaseEquipment.regional_center_id == params.regional_center_id)
    if params.locomotive_model_id is not None:
        conditions.append(RepairCaseEquipment.locomotive_model_id == params.locomotive_model_id)
    if params.component_equipment_id is not None:
        conditions.append(RepairCaseEquipment.component_equipment_id == params.component_equipment_id)
    if params.element_equipment_id is not None:
        conditions.append(RepairCaseEquipment.element_equipment_id == params.element_equipment_id)
    if params.malfunction_id is not None:
        conditions.append(RepairCaseEquipment.malfunction_id == params.malfunction_id)
    if params.repair_type_id is not None:
        conditions.append(RepairCaseEquipment.repair_type_id == params.repair_type_id)
    if params.supplier_id is not None:
        conditions.append(RepairCaseEquipment.supplier_id == params.supplier_id)

    # Статус
    if params.status:
        conditions.append(status_expr == params.status)

    return conditions


def build_warranty_work_conditions(params: CaseFilterParams) -> list[expression.ColumnElement]:
    """WHERE фильтрация для warranty"""
    conditions = []

    # Уведомления
    if params.notification_number:
        conditions.append(WarrantyWork.notification_number.ilike(f"%{params.notification_number}%"))
    if params.notification_date:
        conditions.append(WarrantyWork.notification_date == params.notification_date)

    if params.re_notification_number:
        conditions.append(WarrantyWork.re_notification_number.ilike(f"%{params.re_notification_number}%"))
    if params.re_notification_date:
        conditions.append(WarrantyWork.re_notification_date == params.re_notification_date)

    # Ответ
    if params.response_letter_number:
        conditions.append(WarrantyWork.response_letter_number.ilike(f"%{params.response_letter_number}%"))
    if params.response_letter_date:
        conditions.append(WarrantyWork.response_letter_date == params.response_letter_date)

    # РА/АВР
    if params.claim_act_number:
        conditions.append(WarrantyWork.claim_act_number.ilike(f"%{params.claim_act_number}%"))
    if params.claim_act_date:
        conditions.append(WarrantyWork.claim_act_date == params.claim_act_date)

    if params.work_completion_act_number:
        conditions.append(WarrantyWork.work_completion_act_number.ilike(f"%{params.work_completion_act_number}%"))
    if params.work_completion_act_date:
        conditions.append(WarrantyWork.work_completion_act_date == params.work_completion_act_date)

    # Фильтры по ID
    if params.notification_summary_id is not None:
        conditions.append(WarrantyWork.notification_summary_id == params.notification_summary_id)
    if params.response_summary_id is not None:
        conditions.append(WarrantyWork.response_summary_id == params.response_summary_id)
    if params.decision_summary_id is not None:
        conditions.append(WarrantyWork.decision_summary_id == params.decision_summary_id)

    return conditions