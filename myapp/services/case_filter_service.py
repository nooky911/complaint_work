from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.equipment_malfunctions import Malfunction
from myapp.schemas.cases import CaseList
from myapp.schemas.filters import FilterOptionsResponse
from myapp.schemas.filters import CaseFilterParams
from myapp.database.query_builders.query_case_builders import load_list_relations
from myapp.database.query_builders.query_case_filters import (
    build_repair_case_conditions,
    build_warranty_work_conditions,
)
from myapp.services.case_status_service import CaseStatusService
from myapp.services.reference_service import ReferenceService


class CaseFilterService:
    """Сервис фильтрации с использованием функции БД"""

    @staticmethod
    async def filter_cases(
        session: AsyncSession, params: CaseFilterParams
    ) -> list[CaseList]:
        """Фильтрация случаев с загрузкой статуса"""
        status_subquery = CaseStatusService.build_status_subquery()

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
            status_value = row[1]
            CaseStatusService.enrich_case_with_status_and_creator(
                case_obj, status_value
            )
            cases.append(CaseList.model_validate(case_obj))

        return cases

    @staticmethod
    async def get_filter_options(session: AsyncSession) -> FilterOptionsResponse:
        """Получение опций для фильтров (для выпадающих списков на фронте)"""
        # Получаем справочники для фильтров
        filter_refs = await ReferenceService.get_filter_references(session)
        equipment_refs = await ReferenceService.get_equipment_references(session)
        malfunctions = await session.execute(select(Malfunction))

        # Добавление статуса
        data = {
            **filter_refs,
            **equipment_refs,
            "malfunctions": [
                {"id": m.id, "name": m.name} for m in malfunctions.scalars().all()
            ],
            "new_components": equipment_refs["components"],
            "new_elements": equipment_refs["elements"],
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
