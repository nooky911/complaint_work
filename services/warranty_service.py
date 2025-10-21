from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from models.warranty_work import WarrantyWork
from models.repair_case_equipment import RepairCaseEquipment
from schemas.warranty import WarrantyWorkUpdate, WarrantyWorkResponse


class WarrantyService:

    @staticmethod
    async def _get_warranty_work_with_relations(case_id: int, session: AsyncSession) -> WarrantyWork | None:
        """Внутренний метод для получения WarrantyWork"""
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
    async def get_warranty_by_case(case_id: int, session: AsyncSession) -> WarrantyWorkResponse:
        """Получение данных по рекл. работе."""
        warranty_work = await WarrantyService._get_warranty_work_with_relations(case_id, session)

        if not warranty_work:
            raise HTTPException(status_code=404, detail="Рекламационная работа не найдена")

        return WarrantyWorkResponse.model_validate(warranty_work)


    @staticmethod
    async def update_warranty_work(
            case_id: int,
            warranty_data: WarrantyWorkUpdate,
            session: AsyncSession
            )-> WarrantyWorkResponse:
        """Редактирование"""
        warranty_work = await WarrantyService._get_warranty_work_with_relations(case_id, session)

        if not warranty_work:
            raise HTTPException(status_code=404, detail="Рекламационная работа не найдена")

        update_data = warranty_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(warranty_work, field, value)

        await session.flush()
        return WarrantyWorkResponse.model_validate(warranty_work)