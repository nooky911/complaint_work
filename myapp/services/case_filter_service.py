from sqlalchemy import select, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import (
    WarrantyWork,
    NotificationSummary,
    ResponseSummary,
    DecisionSummary,
)
from myapp.models.auxiliaries import (
    RegionalCenter,
    LocomotiveModel,
    Supplier,
    EquipmentOwner,
    RepairPerformer,
    DestinationType,
    FaultDiscoveryPlace,
    RepairType,
)
from myapp.models.equipment_malfunctions import Equipment, Malfunction
from myapp.schemas.cases import CaseList
from myapp.schemas.filters import FilterOptionsResponse, CaseFilterParams
from myapp.database.query_builders.query_case_builders import load_list_relations
from myapp.database.query_builders.query_case_filters import (
    build_repair_case_conditions,
    build_warranty_work_conditions,
    status_expr,
)
from myapp.services.case_status_service import CaseStatusService


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
        """Получение опций, которые реально есть в базе"""

        # 1. Для простых справочников, привязанных к RepairCaseEquipment
        async def get_used_items(model, fk_column, name_column):
            stmt = (
                select(model.id, name_column)
                .join(RepairCaseEquipment, fk_column == model.id)
                .distinct()
                .order_by(name_column)
            )
            res = await session.execute(stmt)
            return [{"id": row[0], "name": row[1]} for row in res.all()]

        # 2. Для справочников Документации
        async def get_used_warranty_summaries(model, fk_column, name_column):
            stmt = (
                select(model.id, name_column)
                # Соединяем Справочник -> WarrantyWork
                .join(WarrantyWork, fk_column == model.id)
                # Соединяем WarrantyWork -> RepairCaseEquipment (по case_id)
                .join(
                    RepairCaseEquipment, RepairCaseEquipment.id == WarrantyWork.case_id
                )
                .distinct()
                .order_by(name_column)
            )
            res = await session.execute(stmt)
            return [{"id": row[0], "name": row[1]} for row in res.all()]

        # 3. Для уникальных строк (номера локомотивов/уведомлений)
        async def get_distinct_values(column, join_to_main=False):
            stmt = select(distinct(column)).where(column.is_not(None), column != "")
            if join_to_main:
                stmt = stmt.join(
                    RepairCaseEquipment, RepairCaseEquipment.id == WarrantyWork.case_id
                )
            stmt = stmt.order_by(column)
            res = await session.execute(stmt)
            return list(res.scalars().all())

        data = {
            "regional_centers": await get_used_items(
                RegionalCenter,
                RepairCaseEquipment.regional_center_id,
                RegionalCenter.name,
            ),
            "locomotive_models": await get_used_items(
                LocomotiveModel,
                RepairCaseEquipment.locomotive_model_id,
                LocomotiveModel.name,
            ),
            "suppliers": await get_used_items(
                Supplier, RepairCaseEquipment.supplier_id, Supplier.name
            ),
            "malfunctions": await get_used_items(
                Malfunction, RepairCaseEquipment.malfunction_id, Malfunction.name
            ),
            "equipment_owners": await get_used_items(
                EquipmentOwner,
                RepairCaseEquipment.equipment_owner_id,
                EquipmentOwner.name,
            ),
            "performed_by": await get_used_items(
                RepairPerformer,
                RepairCaseEquipment.performed_by_id,
                RepairPerformer.name,
            ),
            "destinations": await get_used_items(
                DestinationType,
                RepairCaseEquipment.destination_id,
                DestinationType.name,
            ),
            "fault_discovered_at": await get_used_items(
                FaultDiscoveryPlace,
                RepairCaseEquipment.fault_discovered_at_id,
                FaultDiscoveryPlace.name,
            ),
            "repair_types": await get_used_items(
                RepairType, RepairCaseEquipment.repair_type_id, RepairType.name
            ),
            # Оборудование
            "components": await get_used_items(
                Equipment, RepairCaseEquipment.component_equipment_id, Equipment.name
            ),
            "elements": await get_used_items(
                Equipment, RepairCaseEquipment.element_equipment_id, Equipment.name
            ),
            # Документация
            "notification_summaries": await get_used_warranty_summaries(
                NotificationSummary,
                WarrantyWork.notification_summary_id,
                NotificationSummary.notification_summary_name,
            ),
            "response_summaries": await get_used_warranty_summaries(
                ResponseSummary,
                WarrantyWork.response_summary_id,
                ResponseSummary.response_summary_name,
            ),
            "decision_summaries": await get_used_warranty_summaries(
                DecisionSummary,
                WarrantyWork.decision_summary_id,
                DecisionSummary.decision_summary_name,
            ),
            "locomotive_numbers": await get_distinct_values(
                RepairCaseEquipment.locomotive_number
            ),
            "notification_numbers": await get_distinct_values(
                WarrantyWork.notification_number, join_to_main=True
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
