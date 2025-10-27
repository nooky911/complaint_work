from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.schemas.cases import CaseCreate, CaseUpdate
from myapp.database.query_builders.query_case_builders import load_detail_relations
from myapp.database.transactional import transactional

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
    async def get_case(session: AsyncSession, case_id: int) -> RepairCaseEquipment | None:
        """Получение подробного случая"""
        return await CaseService._get_case_with_relations(session, case_id)


    @staticmethod
    @transactional
    async def create_case(session: AsyncSession, case_data: CaseCreate) -> RepairCaseEquipment:
        """Создание случая"""
        case = RepairCaseEquipment(**case_data.model_dump())
        case.warranty_work = WarrantyWork()
        session.add(case)

        await session.flush()
        await session.refresh(case)

        return case


    @staticmethod
    @transactional
    async def update_case(session: AsyncSession, case_id: int, case_data: CaseUpdate) -> RepairCaseEquipment | None:
        """Редактирование случая"""
        case = await CaseService._get_case_with_relations(session, case_id)

        if not case:
            return None

        update_data = case_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)

        return case


    @staticmethod
    @transactional
    async def delete_case(session: AsyncSession, case_id: int) -> int:
        """Удаление случая"""
        stmt = delete(RepairCaseEquipment).where(RepairCaseEquipment.id == case_id)
        result = await session.execute(stmt)

        return result.rowcount