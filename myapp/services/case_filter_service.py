import asyncio
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.warranty_work import WarrantyWork
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.auxiliaries import (
    RegionalCenter,
    LocomotiveModel,
    Supplier,
    RepairType,
)
from myapp.models.equipment_malfunctions import Equipment, Malfunction
from myapp.schemas.cases import CaseList
from myapp.schemas.filters import FilterOptionsResponse
from myapp.schemas.filters import CaseFilterParams
from myapp.database.query_builders.query_case_builders import load_list_relations
from myapp.database.query_builders.query_case_filters import (
    build_repair_case_conditions,
    build_warranty_work_conditions,
    status_expr,
)


class CaseFilterService:
    """Сервис фильтрации с использованием функции БД"""

    @staticmethod
    async def filter_cases(
        session: AsyncSession, params: CaseFilterParams
    ) -> list[CaseList]:

        status_subquery = (
            select(status_expr)
            .where(WarrantyWork.case_id == RepairCaseEquipment.id)
            .scalar_subquery()
            .label("calculated_status")
        )

        stmt = select(RepairCaseEquipment, status_subquery)

        stmt = stmt.options(*load_list_relations())

        all_conditions = []
        # Фильтры
        all_conditions.extend(build_repair_case_conditions(params))
        all_conditions.extend(build_warranty_work_conditions(params))

        if all_conditions:
            stmt = stmt.where(and_(*all_conditions))

        stmt = (
            stmt.offset(params.skip)
            .limit(params.limit)
            .order_by(RepairCaseEquipment.date_recorded.desc())
        )

        result = await session.execute(stmt)
        rows = result.unique().all()

        cases = []
        for row in rows:
            case_obj = row[0]
            # Считаем статус
            calculated_val = row[1] or "Ожидает уведомление поставщика"
            case_obj.status = calculated_val

            # Достаем ФИО
            if hasattr(case_obj, "user") and case_obj.user:
                case_obj.creator_full_name = case_obj.user.full_name
            else:
                case_obj.creator_full_name = "Система"

            cases.append(CaseList.model_validate(case_obj))

        return cases

    @staticmethod
    async def get_filter_options(session: AsyncSession) -> FilterOptionsResponse:
        """Получение опций для фильтров (для выпадающих списков на фронте)"""

        # Запросы для всех справочников
        regional_centers_stmt = select(RegionalCenter)
        locomotive_models_stmt = select(LocomotiveModel)
        equipment_stmt = select(Equipment).where(Equipment.parent_id == None)
        elements_stmt = select(Equipment).where(Equipment.parent_id != None)
        malfunctions_stmt = select(Malfunction)
        suppliers_stmt = select(Supplier)
        repair_types_stmt = select(RepairType)

        (
            regional_centers_result,
            locomotive_models_result,
            equipment_result,
            elements_result,
            malfunctions_result,
            suppliers_result,
            repair_types_result,
        ) = await asyncio.gather(
            session.execute(regional_centers_stmt),
            session.execute(locomotive_models_stmt),
            session.execute(equipment_stmt),
            session.execute(elements_stmt),
            session.execute(malfunctions_stmt),
            session.execute(suppliers_stmt),
            session.execute(repair_types_stmt),
        )

        data = {
            "regional_centers": [
                {"id": rc.id, "name": rc.name}
                for rc in regional_centers_result.scalars().all()
            ],
            "locomotive_models": [
                {"id": lm.id, "name": lm.name}
                for lm in locomotive_models_result.scalars().all()
            ],
            "components": [
                {"id": equip.id, "name": equip.name}
                for equip in equipment_result.scalars().all()
            ],
            "elements": [
                {"id": equip.id, "name": equip.name}
                for equip in elements_result.scalars().all()
            ],
            "malfunctions": [
                {"id": m.id, "name": m.name}
                for m in malfunctions_result.scalars().all()
            ],
            "suppliers": [
                {"id": s.id, "name": s.name} for s in suppliers_result.scalars().all()
            ],
            "repair_types": [
                {"id": rt.id, "name": rt.name}
                for rt in repair_types_result.scalars().all()
            ],
            "statuses": [
                "Ожидает уведомление поставщика",
                "Уведомление отправлено",
                "Ответ получен",
                "Решение принято",
                "Ожидает АВР",
                "Ожидает рекламационный акт",
                "Ожидает ответа поставщика",
                "Ожидает повторного уведомления поставщика",
                "Завершено",
            ],
        }

        return FilterOptionsResponse.model_validate(data)
