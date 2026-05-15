from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.schemas.cases import CaseList
from myapp.schemas.filters import CaseFilterParams, FilterOptionsResponse
from myapp.database.query_builders.query_case_filters import build_filtered_case_stmt
from myapp.services.case_status_service import CaseStatusService
from myapp.services.filter_options_service import FilterOptionsService


class CaseFilterService:
    """Сервис для фильтрации случаев и получения опций фильтров"""

    @staticmethod
    async def filter_cases(
        session: AsyncSession, params: CaseFilterParams
    ) -> list[CaseList]:
        """Основной метод фильтрации случаев"""

        # Получить базовый запрос с фильтрами
        stmt = build_filtered_case_stmt(params)

        # Создать виртуальную таблицу (CTE) для сквозной нумерации всех записей в базе
        numbered_cte = select(
            RepairCaseEquipment.id,
            func.row_number()
            .over(order_by=RepairCaseEquipment.id)
            .label("display_number"),
        ).cte("numbered_cases")

        # JOIN нумерацию к запросу и достаем колонку display_number
        stmt = stmt.outerjoin(numbered_cte, RepairCaseEquipment.id == numbered_cte.c.id)
        stmt = stmt.add_columns(numbered_cte.c.display_number)

        # Пагинация
        stmt = stmt.offset(params.skip).limit(params.limit)

        result = await session.execute(stmt)
        rows = result.unique().all()

        cases = []
        for row in rows:
            case_obj = row[0]
            status_value = row[1]
            display_number = row[2]

            CaseStatusService.enrich_case_with_status_and_creator(
                case_obj, status_value
            )

            case_obj.display_number = display_number

            cases.append(CaseList.model_validate(case_obj))

        return cases

    @staticmethod
    async def get_filter_options() -> FilterOptionsResponse:
        """Получить опции фильтров"""
        return await FilterOptionsService.get_filter_options()

    @staticmethod
    async def get_dynamic_filter_options(
        params: CaseFilterParams,
    ) -> FilterOptionsResponse:
        """Получить динамические опции фильтров"""
        return await FilterOptionsService.get_dynamic_filter_options_optimized(params)
