from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from models.warranty_work import WarrantyWork
from models.repair_case_equipment import RepairCaseEquipment
from schemas.warranty import WarrantyWorkUpdate, WarrantyWorkResponse


class WarrantyService:

    @staticmethod
    async def get_warranty_by_case(case_id: int, session: AsyncSession) -> WarrantyWorkResponse:
        """Получение данных по рекл. работе"""
        stmt = (
            select(WarrantyWork)
            .join(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
        )
        result = await session.execute(stmt)
        warranty_work = result.scalar_one_or_none()

        if not warranty_work:
            raise HTTPException(status_code=404, detail="Warranty work not found")

        return WarrantyWorkResponse.model_validate(warranty_work)


    @staticmethod
    async def update_warranty_work(
            case_id: int,
            warranty_data: WarrantyWorkUpdate,
            session: AsyncSession
            )-> WarrantyWorkResponse:
        """Редактирование случая по рекл. работе"""
        stmt = (
            select(WarrantyWork)
            .join(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
        )
        result = await session.execute(stmt)
        warranty_work = result.scalar_one_or_none()

        if not warranty_work:
            raise HTTPException(status_code=404, detail="Warranty work not found")

        update_data = warranty_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(warranty_work, field, value)

        await session.flush()
        return WarrantyWorkResponse.model_validate(warranty_work)
