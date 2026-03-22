from sqlalchemy import func
from myapp.models.warranty_work import WarrantyWork
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.waybill_docs import WaybillDoc

# SQL-выражение для статуса
status_expr = func.calculate_case_status(
    WarrantyWork.notification_summary_id,
    WarrantyWork.response_summary_id,
    WarrantyWork.decision_summary_id,
    WarrantyWork.work_completion_act_number,
    WarrantyWork.claim_act_number,
    WarrantyWork.re_notification_number,
    WarrantyWork.re_notification_date,
    WarrantyWork.notification_date,
    RepairCaseEquipment.repair_type_id,
    RepairCaseEquipment.destination_id,
    WaybillDoc.ttn_from_rc,
    WaybillDoc.ttn_to_supplier,
    WaybillDoc.ttn_replacement,
    WaybillDoc.ttn_from_supplier,
    WarrantyWork.response_letter_number,
    WarrantyWork.research_document,
).label("calculated_status")
