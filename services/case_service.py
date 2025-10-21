from models.repair_case_equipment import RepairCaseEquipment
from models.warranty_work import WarrantyWork
from schemas.cases import CaseCreate, CaseUpdate, CaseList, CaseDetail

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from fastapi import HTTPException


class CaseService:

    @staticmethod
    async def create_case(case_data: CaseCreate, session: AsyncSession) -> RepairCaseEquipment:
        """Создание случая"""
        case = RepairCaseEquipment(**case_data.model_dump())

        case.warranty_work = WarrantyWork()
        session.add(case)
        await session.flush()
        return case


    @staticmethod
    async def get_case(case_id: int, session: AsyncSession) -> CaseDetail:
        """Получение подробного случая"""
        stmt = (
            select(RepairCaseEquipment)
            .options(
                joinedload(RepairCaseEquipment.warranty_work),
                joinedload(RepairCaseEquipment.regional_center),
                joinedload(RepairCaseEquipment.locomotive_model),
                joinedload(RepairCaseEquipment.fault_discovered_at),
                joinedload(RepairCaseEquipment.component_equipment),
                joinedload(RepairCaseEquipment.element_equipment),
                joinedload(RepairCaseEquipment.malfunction),
                joinedload(RepairCaseEquipment.repair_type),
                joinedload(RepairCaseEquipment.performed_by),
                joinedload(RepairCaseEquipment.equipment_owner),
                joinedload(RepairCaseEquipment.destination),
                joinedload(RepairCaseEquipment.supplier),
            )
            .where(RepairCaseEquipment.id == case_id)
        )
        result = await session.execute(stmt)
        case = result.unique().scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        return CaseDetail.model_validate(case)


    @staticmethod
    async def get_cases_list(session: AsyncSession, skip: int = 0, limit: int = 50) -> list[CaseList]:
        """Весь список слуачев"""
        stmt = (
            select(RepairCaseEquipment)
            .options(
                joinedload(RepairCaseEquipment.warranty_work),
                joinedload(RepairCaseEquipment.regional_center),
                joinedload(RepairCaseEquipment.locomotive_model),
                joinedload(RepairCaseEquipment.component_equipment),
                joinedload(RepairCaseEquipment.element_equipment),
                joinedload(RepairCaseEquipment.malfunction),
                joinedload(RepairCaseEquipment.supplier),
            )
            .offset(skip)
            .limit(limit)
            .order_by(RepairCaseEquipment.date_recorded.desc())
        )
        result = await session.execute(stmt)
        cases = result.scalars().all()

        return [CaseList.model_validate(case) for case in cases]


    @staticmethod
    async def update_case(case_id: int, case_data: CaseUpdate, session: AsyncSession) -> CaseDetail:
        """Редактирование случая"""
        stmt = (
            select(RepairCaseEquipment)
            .options(
                joinedload(RepairCaseEquipment.warranty_work),
                joinedload(RepairCaseEquipment.regional_center),
                joinedload(RepairCaseEquipment.locomotive_model),
                joinedload(RepairCaseEquipment.fault_discovered_at),
                joinedload(RepairCaseEquipment.component_equipment),
                joinedload(RepairCaseEquipment.element_equipment),
                joinedload(RepairCaseEquipment.malfunction),
                joinedload(RepairCaseEquipment.repair_type),
                joinedload(RepairCaseEquipment.performed_by),
                joinedload(RepairCaseEquipment.equipment_owner),
                joinedload(RepairCaseEquipment.destination),
                joinedload(RepairCaseEquipment.supplier),
            )
            .where(RepairCaseEquipment.id == case_id)
        )
        result = await session.execute(stmt)
        case = result.unique().scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        update_data = case_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)

        await session.flush()

        return CaseDetail.model_validate(case)


    @staticmethod
    async def delete_case(case_id: int, session: AsyncSession) -> None:
        """Удаление случая"""
        stmt = select(RepairCaseEquipment).where(RepairCaseEquipment.id == case_id)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        await session.delete(case)
        await session.flush()