import asyncio
from sqlalchemy import select, and_, distinct

from myapp.database.base import async_session_maker
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.models.warranty_work import (
    NotificationSummary,
    ResponseSummary,
    DecisionSummary,
)
from myapp.models.user import User
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
from myapp.schemas.filters import FilterOptionsResponse, CaseFilterParams
from myapp.database.query_builders.query_case_filters import (
    build_repair_case_conditions,
    build_warranty_work_conditions,
)
from myapp.services.cache_service import cached
from myapp.constants.filter_constants import STATUSES
from myapp.constants.filter_constants import DB_SEMAPHORE_LIMIT


class FilterOptionsService:
    """Сервис для получения опций фильтров"""

    _db_semaphore = asyncio.Semaphore(DB_SEMAPHORE_LIMIT)

    @staticmethod
    @cached(ttl_seconds=600)
    async def get_filter_options() -> FilterOptionsResponse:

        # Список справочников для быстрой загрузки
        reference_tasks = [
            {
                "name": "regional_centers",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    RegionalCenter,
                    RepairCaseEquipment.regional_center_id,
                    RegionalCenter.regional_center_name,
                ],
            },
            {
                "name": "locomotive_models",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    LocomotiveModel,
                    RepairCaseEquipment.locomotive_model_id,
                    LocomotiveModel.locomotive_model_name,
                ],
            },
            {
                "name": "suppliers",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    Supplier,
                    RepairCaseEquipment.supplier_id,
                    Supplier.supplier_name,
                ],
            },
            {
                "name": "equipment_owners",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    EquipmentOwner,
                    RepairCaseEquipment.equipment_owner_id,
                    EquipmentOwner.equipment_owners_name,
                ],
            },
            {
                "name": "performed_by",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    RepairPerformer,
                    RepairCaseEquipment.performed_by_id,
                    RepairPerformer.repair_performers_name,
                ],
            },
            {
                "name": "destinations",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    DestinationType,
                    RepairCaseEquipment.destination_id,
                    DestinationType.destination_types_name,
                ],
            },
            {
                "name": "fault_discovered_at",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    FaultDiscoveryPlace,
                    RepairCaseEquipment.fault_discovered_at_id,
                    FaultDiscoveryPlace.fault_discovery_places_name,
                ],
            },
            {
                "name": "repair_types",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    RepairType,
                    RepairCaseEquipment.repair_type_id,
                    RepairType.repair_types_name,
                ],
            },
            {
                "name": "malfunctions",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    Malfunction,
                    RepairCaseEquipment.malfunction_id,
                    Malfunction.defect_name,
                ],
            },
            {
                "name": "components",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    Equipment,
                    RepairCaseEquipment.component_equipment_id,
                    Equipment.equipment_name,
                ],
            },
            {
                "name": "elements",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    Equipment,
                    RepairCaseEquipment.element_equipment_id,
                    Equipment.equipment_name,
                ],
            },
            {
                "name": "new_components",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    Equipment,
                    RepairCaseEquipment.new_component_equipment_id,
                    Equipment.equipment_name,
                ],
            },
            {
                "name": "new_elements",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [
                    Equipment,
                    RepairCaseEquipment.new_element_equipment_id,
                    Equipment.equipment_name,
                ],
            },
            {
                "name": "notification_summaries",
                "func": FilterOptionsService._get_all_reference_items_separate_session,
                "args": [
                    NotificationSummary,
                    NotificationSummary.notification_summary_name,
                ],
            },
            {
                "name": "response_summaries",
                "func": FilterOptionsService._get_all_reference_items_separate_session,
                "args": [ResponseSummary, ResponseSummary.response_summary_name],
            },
            {
                "name": "decision_summaries",
                "func": FilterOptionsService._get_all_reference_items_separate_session,
                "args": [DecisionSummary, DecisionSummary.decision_summary_name],
            },
            {
                "name": "users",
                "func": FilterOptionsService._get_used_items_with_case_join,
                "args": [User, RepairCaseEquipment.user_id, User.full_name],
            },
            {
                "name": "locomotive_numbers",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [RepairCaseEquipment.locomotive_number, None],
            },
            {
                "name": "notification_numbers",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [WarrantyWork.notification_number, None],
            },
            {
                "name": "notification_dates",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [WarrantyWork.notification_date, None],
            },
            {
                "name": "re_notification_dates",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [WarrantyWork.re_notification_date, None],
            },
            {
                "name": "response_letter_dates",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [WarrantyWork.response_letter_date, None],
            },
            {
                "name": "claim_act_dates",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [WarrantyWork.claim_act_date, None],
            },
            {
                "name": "work_completion_act_dates",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [WarrantyWork.work_completion_act_date, None],
            },
            {
                "name": "component_serial_numbers",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [RepairCaseEquipment.component_serial_number_old, None],
            },
            {
                "name": "element_serial_numbers",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [RepairCaseEquipment.element_serial_number_old, None],
            },
            {
                "name": "component_serial_numbers_new",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [RepairCaseEquipment.component_serial_number_new, None],
            },
            {
                "name": "element_serial_numbers_new",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [RepairCaseEquipment.element_serial_number_new, None],
            },
            {
                "name": "notes",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [RepairCaseEquipment.notes, None],
            },
        ]

        # Выполняем все задачи параллельно
        task_results = await FilterOptionsService._execute_parallel_tasks_optimized(
            async_session_maker, reference_tasks
        )

        return FilterOptionsService._build_filter_response(task_results)

    @staticmethod
    def _build_filter_response(task_results):
        """Build FilterOptionsResponse from task results"""
        # Формируем результат
        result_dict = {}
        for task_name, items in task_results:
            result_dict[task_name] = items

        if "statuses" not in result_dict:
            result_dict["statuses"] = STATUSES

        return FilterOptionsResponse(**result_dict)

    @staticmethod
    @cached()
    async def get_dynamic_filter_options_optimized(
        params: CaseFilterParams,
    ) -> FilterOptionsResponse:
        """Получает опции фильтров с учетом уже выбранных значений"""
        from myapp.database.base import async_session_maker

        # Условия фильтрации
        repair_conditions = build_repair_case_conditions(params)
        warranty_conditions = build_warranty_work_conditions(params)

        # Задачи для параллельного выполнения
        tasks = [
            {
                "name": "locomotive_numbers",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [RepairCaseEquipment.locomotive_number, repair_conditions],
            },
            {
                "name": "component_serial_numbers",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [
                    RepairCaseEquipment.component_serial_number_old,
                    repair_conditions,
                ],
            },
            {
                "name": "element_serial_numbers",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [
                    RepairCaseEquipment.element_serial_number_old,
                    repair_conditions,
                ],
            },
            {
                "name": "component_serial_numbers_new",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [
                    RepairCaseEquipment.component_serial_number_new,
                    repair_conditions,
                ],
            },
            {
                "name": "element_serial_numbers_new",
                "func": FilterOptionsService._get_distinct_values_separate_session,
                "args": [
                    RepairCaseEquipment.element_serial_number_new,
                    repair_conditions,
                ],
            },
            {
                "name": "regional_centers",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    RegionalCenter,
                    RepairCaseEquipment.regional_center_id,
                    RegionalCenter.regional_center_name,
                    repair_conditions + warranty_conditions,
                ],
            },
            {
                "name": "locomotive_models",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    LocomotiveModel,
                    RepairCaseEquipment.locomotive_model_id,
                    LocomotiveModel.locomotive_model_name,
                    repair_conditions + warranty_conditions,
                ],
            },
            {
                "name": "suppliers",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    Supplier,
                    RepairCaseEquipment.supplier_id,
                    Supplier.supplier_name,
                    repair_conditions + warranty_conditions,
                ],
            },
            {
                "name": "equipment_owners",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    EquipmentOwner,
                    RepairCaseEquipment.equipment_owner_id,
                    EquipmentOwner.equipment_owners_name,
                    repair_conditions + warranty_conditions,
                ],
            },
            {
                "name": "performed_by",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    RepairPerformer,
                    RepairCaseEquipment.performed_by_id,
                    RepairPerformer.repair_performers_name,
                    repair_conditions + warranty_conditions,
                ],
            },
            {
                "name": "destinations",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    DestinationType,
                    RepairCaseEquipment.destination_id,
                    DestinationType.destination_types_name,
                    repair_conditions + warranty_conditions,
                ],
            },
            {
                "name": "fault_discovered_at",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    FaultDiscoveryPlace,
                    RepairCaseEquipment.fault_discovered_at_id,
                    FaultDiscoveryPlace.fault_discovery_places_name,
                    repair_conditions + warranty_conditions,
                ],
            },
            {
                "name": "repair_types",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    RepairType,
                    RepairCaseEquipment.repair_type_id,
                    RepairType.repair_types_name,
                    repair_conditions + warranty_conditions,
                ],
            },
            # Оборудование и неисправности
            {
                "name": "components",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    Equipment,
                    RepairCaseEquipment.component_equipment_id,
                    Equipment.equipment_name,
                    repair_conditions + warranty_conditions,
                ],
            },
            {
                "name": "elements",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    Equipment,
                    RepairCaseEquipment.element_equipment_id,
                    Equipment.equipment_name,
                    repair_conditions + warranty_conditions,
                ],
            },
            {
                "name": "malfunctions",
                "func": FilterOptionsService._get_used_items_with_warranty_join,
                "args": [
                    Malfunction,
                    RepairCaseEquipment.malfunction_id,
                    Malfunction.defect_name,
                    repair_conditions + warranty_conditions,
                ],
            },
        ]

        task_results = await FilterOptionsService._execute_parallel_tasks_optimized(
            async_session_maker, tasks
        )

        return FilterOptionsService._build_filter_response(task_results)

    @staticmethod
    async def _execute_parallel_tasks_optimized(session_factory, task_configs):
        """
        Запускает все задачи сразу, но их количество ограничивается только глобальным семафором
        """

        async def run_task(config):
            async with session_factory() as session:
                all_args = [session] + config["args"]
                return await FilterOptionsService._execute_with_semaphore(
                    config["func"],
                    all_args,
                    config.get("kwargs", {}),
                    operation_name=config["name"],
                )

        tasks = [run_task(cfg) for cfg in task_configs]
        return await asyncio.gather(*tasks)

    @staticmethod
    async def _execute_with_semaphore(func, args, kwargs, operation_name: str):
        """Выполняет функцию ТОЛЬКО после получения разрешения от семафора"""
        async with FilterOptionsService._db_semaphore:
            result = await func(*args, **kwargs)
            return operation_name, result

    @staticmethod
    async def _get_used_items_with_warranty_join(
        session,
        model,
        fk_column,
        name_column,
        filtered_conditions=None,
    ):
        """Получить используемые элементы справочника с JOIN к WarrantyWork"""
        stmt = (
            select(model.id, name_column)
            .join(RepairCaseEquipment, fk_column == model.id)
            .join(WarrantyWork, WarrantyWork.case_id == RepairCaseEquipment.id)
            .distinct()
        )

        if filtered_conditions:
            stmt = stmt.where(and_(*filtered_conditions))

        res = await session.execute(stmt)
        return [{"id": row[0], "name": row[1]} for row in res.all()]

    @staticmethod
    async def _get_used_items_with_case_join(
        session,
        model,
        fk_column,
        name_column,
        filtered_conditions=None,
    ):
        """Получить используемые элементы справочника на основе RepairCaseEquipment"""
        stmt = (
            select(model.id, name_column)
            .join(RepairCaseEquipment, fk_column == model.id)
            .distinct()
        )

        if filtered_conditions:
            stmt = stmt.where(and_(*filtered_conditions))

        res = await session.execute(stmt)
        return [{"id": row[0], "name": row[1]} for row in res.all()]

    @staticmethod
    async def _get_distinct_values_separate_session(
        session,
        column,
        filtered_conditions=None,
    ):
        """Получить уникальные значения колонки"""
        return await FilterOptionsService._get_distinct_values_core(
            session, column, filtered_conditions
        )

    @staticmethod
    async def _get_distinct_values_core(
        session,
        column,
        filtered_conditions=None,
    ):
        """Получить уникальные значения колонки - основная реализация"""
        stmt = select(distinct(column)).where(column.isnot(None))

        if filtered_conditions:
            stmt = stmt.where(and_(*filtered_conditions))

        res = await session.execute(stmt)
        values = [row[0] for row in res.all() if row[0] is not None]
        return values

    @staticmethod
    async def _get_all_reference_items_separate_session(session, model, name_column):
        """Получить все элементы справочника без JOIN"""
        stmt = select(model.id, name_column)
        res = await session.execute(stmt)
        return [{"id": row[0], "name": row[1]} for row in res.all()]
