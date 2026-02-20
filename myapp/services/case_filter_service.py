from sqlalchemy import select, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.user import User
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
)
from myapp.services.case_status_service import CaseStatusService


class CaseFilterService:
    """Сервис фильтрации по всем полям RepairCase и WarrantyWork"""

    @staticmethod
    async def filter_cases(
        session: AsyncSession, params: CaseFilterParams
    ) -> list[CaseList]:
        status_subquery = CaseStatusService.build_status_subquery()

        stmt = select(RepairCaseEquipment, status_subquery)
        stmt = stmt.options(*load_list_relations())

        stmt = stmt.outerjoin(RepairCaseEquipment.warranty_work)

        repair_conditions = build_repair_case_conditions(params)
        warranty_conditions = build_warranty_work_conditions(params)

        all_conditions = repair_conditions + warranty_conditions

        if params.section_mask is not None and params.section_mask > 0:
            all_conditions.append(
                RepairCaseEquipment.section_mask == params.section_mask
            )

        if params.status:
            all_conditions.append(status_subquery.in_(params.status))

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
            "locomotive_numbers": await get_distinct_values(
                RepairCaseEquipment.locomotive_number
            ),
            "section_masks": [
                {"id": 1, "name": "А"},
                {"id": 2, "name": "Б"},
                {"id": 4, "name": "Бустер"},
            ],
            "regional_centers": await get_used_items(
                RegionalCenter,
                RepairCaseEquipment.regional_center_id,
                RegionalCenter.regional_center_name,
            ),
            "locomotive_models": await get_used_items(
                LocomotiveModel,
                RepairCaseEquipment.locomotive_model_id,
                LocomotiveModel.locomotive_model_name,
            ),
            "suppliers": await get_used_items(
                Supplier, RepairCaseEquipment.supplier_id, Supplier.supplier_name
            ),
            "malfunctions": await get_used_items(
                Malfunction, RepairCaseEquipment.malfunction_id, Malfunction.defect_name
            ),
            "equipment_owners": await get_used_items(
                EquipmentOwner,
                RepairCaseEquipment.equipment_owner_id,
                EquipmentOwner.equipment_owners_name,
            ),
            "performed_by": await get_used_items(
                RepairPerformer,
                RepairCaseEquipment.performed_by_id,
                RepairPerformer.repair_performers_name,
            ),
            "destinations": await get_used_items(
                DestinationType,
                RepairCaseEquipment.destination_id,
                DestinationType.destination_types_name,
            ),
            "fault_discovered_at": await get_used_items(
                FaultDiscoveryPlace,
                RepairCaseEquipment.fault_discovered_at_id,
                FaultDiscoveryPlace.fault_discovery_places_name,
            ),
            "repair_types": await get_used_items(
                RepairType,
                RepairCaseEquipment.repair_type_id,
                RepairType.repair_types_name,
            ),
            # Оборудование
            "components": await get_used_items(
                Equipment,
                RepairCaseEquipment.component_equipment_id,
                Equipment.equipment_name,
            ),
            "elements": await get_used_items(
                Equipment,
                RepairCaseEquipment.element_equipment_id,
                Equipment.equipment_name,
            ),
            "component_serial_numbers": await get_distinct_values(
                RepairCaseEquipment.component_serial_number_old
            ),
            "element_serial_numbers": await get_distinct_values(
                RepairCaseEquipment.element_serial_number_old
            ),
            "new_components": await get_used_items(
                Equipment,
                RepairCaseEquipment.new_component_equipment_id,
                Equipment.equipment_name,
            ),
            "new_elements": await get_used_items(
                Equipment,
                RepairCaseEquipment.new_element_equipment_id,
                Equipment.equipment_name,
            ),
            "notes": await get_distinct_values(RepairCaseEquipment.notes),
            # Документация
            "notification_numbers": await get_distinct_values(
                WarrantyWork.notification_number, join_to_main=True
            ),
            "re_notification_numbers": await get_distinct_values(
                WarrantyWork.re_notification_number, join_to_main=True
            ),
            "response_letter_numbers": await get_distinct_values(
                WarrantyWork.response_letter_number, join_to_main=True
            ),
            "claim_act_numbers": await get_distinct_values(
                WarrantyWork.claim_act_number, join_to_main=True
            ),
            "work_completion_act_numbers": await get_distinct_values(
                WarrantyWork.work_completion_act_number, join_to_main=True
            ),
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
            "users": await get_used_items(User, User.id, User.full_name),
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
