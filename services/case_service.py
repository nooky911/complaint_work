from models.repair_case_equipment import RepairCaseEquipment
from models.warranty_work import WarrantyWork, NotificationSummary, ResponseSummary, DecisionSummary
from schemas.cases import CaseCreate, CaseUpdate, CaseList, CaseDetail
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from fastapi import HTTPException


class CaseService:

    @staticmethod
    async def _get_case_with_relations(session: AsyncSession, case_id: int) -> RepairCaseEquipment | None:
        stmt = (
            select(RepairCaseEquipment)
            .options(
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

                # warranty_work
                joinedload(RepairCaseEquipment.warranty_work)
                .selectinload(WarrantyWork.notification_summary)
                .selectinload(WarrantyWork.response_summary)
                .selectinload(WarrantyWork.decision_summary),
            )
            .where(RepairCaseEquipment.id == case_id)
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

    # ---

    @staticmethod
    async def create_case(case_data: CaseCreate, session: AsyncSession) -> RepairCaseEquipment:
        """Создание случая"""
        case = RepairCaseEquipment(**case_data.model_dump())

        # Создаем связанную запись WarrantyWork
        case.warranty_work = WarrantyWork()
        session.add(case)
        await session.flush()
        return case


    @staticmethod
    async def get_case(case_id: int, session: AsyncSession) -> CaseDetail:
        """Получение подробного случая"""
        case = await CaseService._get_case_with_relations(session, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        return CaseDetail.model_validate(case)


    @staticmethod
    async def get_cases_list(session: AsyncSession, skip: int = 0, limit: int = 50) -> List[CaseList]:
        """Список случаев"""
        stmt = (
            select(RepairCaseEquipment)
            .options(
                selectinload(RepairCaseEquipment.warranty_work),
                selectinload(RepairCaseEquipment.regional_center),
                selectinload(RepairCaseEquipment.locomotive_model),
                selectinload(RepairCaseEquipment.component_equipment),
                selectinload(RepairCaseEquipment.element_equipment),
                selectinload(RepairCaseEquipment.malfunction),
                selectinload(RepairCaseEquipment.supplier),
            )
            .offset(skip)
            .limit(limit)
            .order_by(RepairCaseEquipment.date_recorded.desc())
        )
        result = await session.execute(stmt)
        cases = result.unique().scalars().all()

        return [CaseList.model_validate(case) for case in cases]


    @staticmethod
    async def update_case(case_id: int, case_data: CaseUpdate, session: AsyncSession) -> CaseDetail:
        """Редактирование случая"""
        case = await CaseService._get_case_with_relations(session, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        update_data = case_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)

        await session.flush()
        # Возвращаем полностью загруженный объект
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