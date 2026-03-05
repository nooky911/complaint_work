import asyncio
from sqlalchemy import select

from myapp.database.base import async_session_maker
from myapp.services.cache_service import cached
from myapp.constants.filter_constants import DB_SEMAPHORE_LIMIT
from myapp.models.auxiliaries import (
    RegionalCenter,
    LocomotiveModel,
    Supplier,
    RepairType,
    FaultDiscoveryPlace,
    EquipmentOwner,
    RepairPerformer,
    DestinationType,
)
from myapp.models.equipment_malfunctions import (
    Malfunction,
    EquipmentMalfunction,
)
from myapp.models.warranty_work import (
    NotificationSummary,
    ResponseSummary,
    DecisionSummary,
)


class ReferenceService:
    """Сервис для работы со справочниками"""

    _db_semaphore = asyncio.Semaphore(DB_SEMAPHORE_LIMIT)

    @staticmethod
    def _map_to_id_name(rows):
        """Вспомогательная функция для формирования стандартного списка id/name"""
        return [{"id": r[0], "name": r[1]} for r in rows]

    @staticmethod
    @cached(ttl_seconds=600)
    async def get_case_form_references():
        """Получить ВСЕ справочники для формы создания/редактирования случая"""

        tasks = [
            (
                "regional_centers",
                select(RegionalCenter.id, RegionalCenter.regional_center_name),
            ),
            (
                "locomotive_models",
                select(
                    LocomotiveModel.id, LocomotiveModel.locomotive_model_name
                ),
            ),
            (
                "fault_discovery_places",
                select(
                    FaultDiscoveryPlace.id,
                    FaultDiscoveryPlace.fault_discovery_places_name,
                ),
            ),
            (
                "repair_types",
                select(
                    RepairType.id,
                    RepairType.repair_types_name,
                    RepairType.auto_fill_strategy,
                ),
            ),
            (
                "equipment_owners",
                select(
                    EquipmentOwner.id, EquipmentOwner.equipment_owners_name
                ),
            ),
            (
                "repair_performers",
                select(
                    RepairPerformer.id, RepairPerformer.repair_performers_name
                ),
            ),
            (
                "destination_types",
                select(
                    DestinationType.id, DestinationType.destination_types_name
                ),
            ),
            (
                "malfunctions",
                select(Malfunction.id, Malfunction.defect_name),
            ),
            (
                "suppliers",
                select(Supplier.id, Supplier.supplier_name),
            ),
            (
                "notification_summaries",
                select(
                    NotificationSummary.id,
                    NotificationSummary.notification_summary_name,
                ),
            ),
            (
                "response_summaries",
                select(
                    ResponseSummary.id, ResponseSummary.response_summary_name
                ),
            ),
            (
                "decision_summaries",
                select(
                    DecisionSummary.id, DecisionSummary.decision_summary_name
                ),
            ),
            (
                "equipment_malfunctions",
                select(
                    EquipmentMalfunction.equipment_id,
                    EquipmentMalfunction.malfunction_id,
                ),
            ),
        ]

        async def run_query(name, stmt):
            async with ReferenceService._db_semaphore:
                async with async_session_maker() as session:
                    result = await session.execute(stmt)
                    return name, result.all()

        results = await asyncio.gather(*(run_query(name, stmt) for name, stmt in tasks))
        res_dict = {name: rows for name, rows in results}

        return {
            "regional_centers": ReferenceService._map_to_id_name(
                res_dict["regional_centers"]
            ),
            "locomotive_models": ReferenceService._map_to_id_name(
                res_dict["locomotive_models"]
            ),
            "fault_discovered_at": ReferenceService._map_to_id_name(
                res_dict["fault_discovery_places"]
            ),
            "repair_types": [
                {"id": r[0], "name": r[1], "auto_fill_strategy": r[2]}
                for r in res_dict["repair_types"]
            ],
            "equipment_owners": ReferenceService._map_to_id_name(
                res_dict["equipment_owners"]
            ),
            "performed_by": ReferenceService._map_to_id_name(
                res_dict["repair_performers"]
            ),
            "destinations": ReferenceService._map_to_id_name(
                res_dict["destination_types"]
            ),
            "malfunctions": ReferenceService._map_to_id_name(res_dict["malfunctions"]),
            "equipment_malfunctions": [
                {"equipment_id": r[0], "malfunction_id": r[1]}
                for r in res_dict["equipment_malfunctions"]
            ],
            "suppliers": ReferenceService._map_to_id_name(res_dict["suppliers"]),
            "notification_summaries": ReferenceService._map_to_id_name(
                res_dict["notification_summaries"]
            ),
            "response_summaries": ReferenceService._map_to_id_name(
                res_dict["response_summaries"]
            ),
            "decision_summaries": ReferenceService._map_to_id_name(
                res_dict["decision_summaries"]
            ),
        }
