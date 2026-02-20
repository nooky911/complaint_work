from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.warranty_work import WarrantyWork
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.database.query_builders.expressions import status_expr


class CaseStatusService:
    """Сервис для работы со статусами случаев"""

    @staticmethod
    def build_status_subquery():
        """Создает подзапрос для вычисления статуса"""
        return (
            select(status_expr)
            .select_from(WarrantyWork)
            .where(WarrantyWork.case_id == RepairCaseEquipment.id)
            .correlate(RepairCaseEquipment)
            .scalar_subquery()
            .label("calculated_status")
        )

    @staticmethod
    async def get_case_status(session: AsyncSession, case_id: int) -> str:
        """Получает статус конкретного случая"""
        status_stmt = (
            select(status_expr)
            .select_from(WarrantyWork)
            .where(WarrantyWork.case_id == case_id)
        )
        result = await session.execute(status_stmt)
        status_value = result.scalar_one_or_none()
        return status_value or "Ожидает уведомление поставщика"

    @staticmethod
    def enrich_case_with_status_and_creator(case_obj, status_value):
        """Добавляет статус и ФИО создателя"""
        case_obj.status = status_value or "Ожидает уведомление поставщика"

        if hasattr(case_obj, "user") and case_obj.user:
            case_obj.creator_full_name = case_obj.user.full_name
        else:
            case_obj.creator_full_name = "Система"

        return case_obj

    @staticmethod
    async def get_case_with_status(
        session: AsyncSession, case_id: int, relations_loader
    ) -> RepairCaseEquipment | None:
        """Универсальный метод для загрузки случая со статусом"""
        status_subquery = CaseStatusService.build_status_subquery()

        stmt = select(RepairCaseEquipment, status_subquery)
        stmt = stmt.options(*relations_loader())
        stmt = stmt.where(RepairCaseEquipment.id == case_id)

        result = await session.execute(stmt)
        row = result.first()

        if row:
            case = row[0]
            status_value = row[1]
            return CaseStatusService.enrich_case_with_status_and_creator(
                case, status_value
            )
        return None
