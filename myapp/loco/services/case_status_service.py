from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.warranty_work import WarrantyWork
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.waybill_docs import WaybillDoc
from myapp.database.query_builders.expressions import status_expr, train_status_expr


class CaseStatusService:
    """Сервис для работы со статусами случаев"""

    @staticmethod
    def build_status_subquery(direction="loco"):
        """Создает подзапрос для вычисления статуса"""
        return (
            select(train_status_expr if direction == "train" else status_expr)
            .select_from(WarrantyWork)
            .outerjoin(WaybillDoc, WaybillDoc.case_id == WarrantyWork.case_id)
            .where(WarrantyWork.case_id == RepairCaseEquipment.id)
            .correlate(RepairCaseEquipment)
            .scalar_subquery()
            .label("calculated_status")
        )

    @staticmethod
    def enrich_case_with_status_and_creator(
        case_obj, status_value
    ) -> RepairCaseEquipment:
        """Добавляет статус и ФИО создателя"""
        case_obj.status = status_value or "Ожидает отправки уведомления поставщику"

        if hasattr(case_obj, "user") and case_obj.user:
            case_obj.creator_full_name = case_obj.user.full_name
        else:
            case_obj.creator_full_name = "Система"

        return case_obj

    @staticmethod
    async def get_case_with_status(
        session: AsyncSession, case_id: int, relations_loader, direction="loco"
    ) -> RepairCaseEquipment | None:
        """Универсальный метод для загрузки случая со статусом"""
        status_subquery = CaseStatusService.build_status_subquery(direction)

        stmt = select(RepairCaseEquipment, status_subquery)
        stmt = stmt.options(*relations_loader())
        stmt = stmt.where(RepairCaseEquipment.id == case_id, RepairCaseEquipment.direction == direction)
        stmt = stmt.execution_options(populate_existing=True)

        result = await session.execute(stmt)
        row = result.first()

        if row:
            case = row[0]
            status_value = row[1]
            return CaseStatusService.enrich_case_with_status_and_creator(
                case, status_value
            )
        return None
