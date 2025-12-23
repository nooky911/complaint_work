from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.schemas.cases import CaseCreate, CaseUpdate
from myapp.database.query_builders.query_case_builders import load_detail_relations
from myapp.database.query_builders.query_case_filters import status_expr
from myapp.database.transactional import transactional
from myapp.services.equipment_service import EquipmentService
from myapp.services.warranty_service import WarrantyService


class CaseService:

    @staticmethod
    async def _get_case_with_relations(
        session: AsyncSession, case_id: int
    ) -> RepairCaseEquipment | None:
        """Внутренний метод для загрузки случая со всеми связями"""
        stmt = (
            select(RepairCaseEquipment, status_expr)
            .options(*load_detail_relations())
            .outerjoin(RepairCaseEquipment.warranty_work)
            .where(RepairCaseEquipment.id == case_id)
        )
        result = await session.execute(stmt)

        row = result.first()

        if row:
            case = row[0]
            calculated_status = row[1]

            # Прикрепляем вычисленное поле к объекту ORM для Pydantic
            setattr(case, "calculated_status", calculated_status)
            return case
        return None

    @staticmethod
    async def get_case(
        session: AsyncSession, case_id: int
    ) -> RepairCaseEquipment | None:
        """Получение подробного случая"""
        return await CaseService._get_case_with_relations(session, case_id)

    @staticmethod
    @transactional
    async def create_case(
        session: AsyncSession,
        case_data: CaseCreate,
        user_id: int,
    ) -> RepairCaseEquipment:
        """Создание случая"""

        # 1. Разделяем данные: извлекаем вложенную модель warranty_work
        case_creation_data = case_data.model_dump(exclude={"warranty_work"})
        warranty_work_data = (
            case_data.warranty_work.model_dump(exclude_unset=True)
            if case_data.warranty_work
            else {}
        )

        # 2. Создаем RepairCaseEquipment только с его собственными полями
        case = RepairCaseEquipment(**case_creation_data)
        case.date_recorded = datetime.now()
        case.user_id = user_id

        # 3. Создаем WarrantyWork и привязываем его как ORM-объект
        new_warranty_work = WarrantyWork(**warranty_work_data)
        case.warranty_work = new_warranty_work

        # 4. Пересчет supplier_id
        if case.component_equipment_id:
            supplier_id = await EquipmentService.find_supplier_in_parents(
                session, case.component_equipment_id
            )
            case.supplier_id = supplier_id

        session.add(case)
        await session.flush()

        # 5. Получаем объект со всеми связями и вычисленным статусом
        created_case = await CaseService._get_case_with_relations(session, case.id)
        return created_case

    @staticmethod
    @transactional
    async def update_case(
        session: AsyncSession, case_id: int, case_data: CaseUpdate
    ) -> RepairCaseEquipment | None:
        """Обновление случая, включая WarrantyWork, и автоматическое переопределение supplier_id"""
        case: RepairCaseEquipment | None = await session.get(
            RepairCaseEquipment, case_id
        )
        if not case:
            return None

        # Автоматически определяем supplier_id если изменился component_equipment_id
        supplier_id = case.supplier_id

        # Если в обновлении передали component_equipment_id, переопределяем supplier_id
        if case_data.component_equipment_id is not None:
            supplier_id = await EquipmentService.find_supplier_in_parents(
                session, case_data.component_equipment_id
            )

        update_data = case_data.model_dump(
            exclude_unset=True, exclude={"warranty_work"}
        )
        update_data["supplier_id"] = supplier_id

        for field, value in update_data.items():
            setattr(case, field, value)

        await session.flush()

        # Обновление WarrantyWork
        if case_data.warranty_work:
            await WarrantyService.update_warranty_work(
                session, case_id, case_data.warranty_work
            )

        return await CaseService._get_case_with_relations(session, case.id)

    @staticmethod
    @transactional
    async def delete_case(session: AsyncSession, case_id: int) -> int:
        """Удаление случая"""
        stmt = delete(RepairCaseEquipment).where(RepairCaseEquipment.id == case_id)
        result = await session.execute(stmt)
        return result.rowcount
