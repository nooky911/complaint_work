from sqlalchemy import func
from myapp.models.warranty_work import WarrantyWork

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
).label("calculated_status")
