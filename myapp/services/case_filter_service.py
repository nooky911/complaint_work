from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.schemas.cases import CaseList
from myapp.schemas.filters import CaseFilterParams, FilterOptionsResponse
from myapp.database.query_builders.query_case_builders import load_list_relations
from myapp.database.query_builders.query_case_filters import (
    build_repair_case_conditions,
    build_warranty_work_conditions,
)
from myapp.services.case_status_service import CaseStatusService
from myapp.services.filter_options_service import FilterOptionsService


class CaseFilterService:
    """Сервис для фильтрации случаев и получения опций фильтров"""

    @staticmethod
    async def filter_cases(
        session: AsyncSession, params: CaseFilterParams
    ) -> list[CaseList]:
        """Основной метод фильтрации случаев"""
        status_subquery = CaseStatusService.build_status_subquery()

        stmt = select(RepairCaseEquipment, status_subquery)

        stmt = stmt.options(*load_list_relations())

        stmt = stmt.outerjoin(RepairCaseEquipment.warranty_work)

        all_conditions = []
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
    async def get_filter_options() -> FilterOptionsResponse:
        """Получить опции фильтров"""
        return await FilterOptionsService.get_filter_options()

    @staticmethod
    async def get_dynamic_filter_options(
        params: CaseFilterParams,
    ) -> FilterOptionsResponse:
        """Получить динамические опции фильтров"""
        return await FilterOptionsService.get_dynamic_filter_options_optimized(params)
