from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from myapp.models.warranty_work import WarrantyWork
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.schemas.warranty import WarrantyWorkUpdate


class WarrantyService:

    @staticmethod
    async def _get_warranty_work_with_relations(case_id: int, session: AsyncSession) -> WarrantyWork | None:
        """Внутренний метод для получения WarrantyWork со связями"""
        stmt = (
            select(WarrantyWork)
            .options(
                joinedload(WarrantyWork.notification_summary),
                joinedload(WarrantyWork.response_summary),
                joinedload(WarrantyWork.decision_summary),
            )
            .join(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()


    @staticmethod
    async def get_warranty_by_case(session: AsyncSession, case_id: int) -> WarrantyWork | None:
        """Получение данных по рекл. работе"""
        return await WarrantyService._get_warranty_work_with_relations(case_id, session)


    @staticmethod
    async def update_warranty_work(
            session: AsyncSession,
            case_id: int,
            warranty_data: WarrantyWorkUpdate
    ) -> WarrantyWork | None:
        """Редактирование"""
        warranty_work = await WarrantyService._get_warranty_work_with_relations(case_id, session)

        if not warranty_work:
            return None

        # Обновление данных
        update_data = warranty_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(warranty_work, field, value)

        return warranty_work