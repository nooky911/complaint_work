from sqlalchemy import select, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.schemas.cases import CaseList
from myapp.schemas.filters import FilterOptionsResponse, CaseFilterParams
from myapp.database.query_builders.query_case_builders import load_list_relations
from myapp.database.query_builders.query_case_filters import (
    build_repair_case_conditions,
    build_warranty_work_conditions,
    status_expr,
)
from myapp.services.case_status_service import CaseStatusService
from myapp.services.reference_service import ReferenceService


class CaseFilterService:
    """Сервис фильтрации по всем полям RepairCase и WarrantyWork"""

    @staticmethod
    async def filter_cases(
        session: AsyncSession, params: CaseFilterParams
    ) -> list[CaseList]:
        """Фильтрация случаев с поддержкой мульти-выбора (массивов)"""
        status_subquery = CaseStatusService.build_status_subquery()

        # Начинаем выборку
        stmt = select(RepairCaseEquipment, status_subquery)
        stmt = stmt.options(*load_list_relations())

        # Собираем условия из двух строителей
        repair_conditions = build_repair_case_conditions(params)
        warranty_conditions = build_warranty_work_conditions(params)

        # Если есть условия для WarrantyWork или фильтр по статусу, нужен JOIN
        if warranty_conditions or params.status:
            stmt = stmt.join(RepairCaseEquipment.warranty_work)

        all_conditions = repair_conditions + warranty_conditions

        # Фильтрация по рассчитанному статусу (через SQL функцию)
        if params.status:
            all_conditions.append(status_expr.in_(params.status))

        if all_conditions:
            stmt = stmt.where(and_(*all_conditions))

        # Сортировка и пагинация
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
        """Получение опций для фильтров"""
        # 1. Базовые справочники из ReferenceService
        form_refs = await ReferenceService.get_case_form_references(session)
        equipment_refs = await ReferenceService.get_equipment_references(session)

        # 2. Получаем уникальные значения строк
        async def get_distinct_values(column):
            res = await session.execute(
                select(distinct(column))
                .where(column.is_not(None), column != "")
                .order_by(column)
            )
            return list(res.scalars().all())

        # Собираем данные для FilterOptionsResponse
        data = {
            **form_refs,
            "components": equipment_refs["components"],
            "elements": equipment_refs["elements"],
            "new_components": equipment_refs["components"],
            "new_elements": equipment_refs["elements"],
            "locomotive_numbers": await get_distinct_values(
                RepairCaseEquipment.locomotive_number
            ),
            "notification_numbers": await get_distinct_values(
                WarrantyWork.notification_number
            ),
            "statuses": [
                "Ожидает уведомление поставщика",
                "Уведомление отправлено",
                "Ответ получен",
                "Решение принято",
                "Ожидает АВР",
                "Завершено",
            ],
        }

        return FilterOptionsResponse.model_validate(data)
