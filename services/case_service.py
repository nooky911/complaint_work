from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from models.repair_case_equipment import RepairCaseEquipment
from models.warranty_work import WarrantyWork
from schemas.cases import CaseCreate, CaseUpdate, CaseDetail
from database.query_builders.query_case_builders import load_detail_relations


class CaseService:

    @staticmethod
    async def _get_case_with_relations(session: AsyncSession, case_id: int) -> RepairCaseEquipment | None:
        """Внутренний метод для загрузки случая со всеми связями"""
        stmt = (
            select(RepairCaseEquipment)
            .options(*load_detail_relations())
            .where(RepairCaseEquipment.id == case_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


    @staticmethod
    async def create_case(case_data: CaseCreate, session: AsyncSession) -> CaseDetail:
        """Создание случая"""
        case = RepairCaseEquipment(**case_data.model_dump())
        case.warranty_work = WarrantyWork()
        session.add(case)

        await session.flush()
        await session.refresh(case)

        full_case = await CaseService._get_case_with_relations(session, case.id)
        if not full_case:
            raise HTTPException(status_code=500, detail="Ошибка при создании случая")

        return CaseDetail.model_validate(full_case)


    @staticmethod
    async def get_case(case_id: int, session: AsyncSession) -> CaseDetail:
        """Получение подробного случая"""
        case = await CaseService._get_case_with_relations(session, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        return CaseDetail.model_validate(case)


    @staticmethod
    async def update_case(case_id: int, case_data: CaseUpdate, session: AsyncSession) -> CaseDetail:
        """Редактирование случая"""
        case = await CaseService._get_case_with_relations(session, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Случай не найден")

        update_data = case_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)

        full_case = await CaseService._get_case_with_relations(session, case.id)

        if not full_case:
            raise HTTPException(status_code=500, detail="Ошибка при обновлении и повторной загрузке")

        return CaseDetail.model_validate(full_case)


    @staticmethod
    async def delete_case(case_id: int, session: AsyncSession) -> None:
        """Удаление случая"""
        stmt = select(RepairCaseEquipment).where(RepairCaseEquipment.id == case_id)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="Случай не найден")

        await session.delete(case)
        await session.flush()