import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from myapp.models.equipment_malfunctions import Equipment, Malfunction
from myapp.models.warranty_work import (
    NotificationSummary,
    ResponseSummary,
    DecisionSummary,
)


class ReferenceService:
    """Сервис для работы со справочниками"""

    @staticmethod
    async def get_case_form_references(session: AsyncSession):
        """Получить ВСЕ справочники для формы создания/редактирования случая"""
        (
            regional_centers_result,
            locomotive_models_result,
            fault_discovery_places_result,
            repair_types_result,
            equipment_owners_result,
            repair_performers_result,
            destination_types_result,
            malfunctions_result,
            suppliers_result,
            notification_summaries_result,
            response_summaries_result,
            decision_summaries_result,
        ) = await asyncio.gather(
            session.execute(select(RegionalCenter)),
            session.execute(select(LocomotiveModel)),
            session.execute(select(FaultDiscoveryPlace)),
            session.execute(select(RepairType)),
            session.execute(select(EquipmentOwner)),
            session.execute(select(RepairPerformer)),
            session.execute(select(DestinationType)),
            session.execute(select(Malfunction)),
            session.execute(select(Supplier)),
            session.execute(select(NotificationSummary)),
            session.execute(select(ResponseSummary)),
            session.execute(select(DecisionSummary)),
        )

        return {
            "regional_centers": [
                {"id": rc.id, "name": rc.name}
                for rc in regional_centers_result.scalars().all()
            ],
            "locomotive_models": [
                {"id": lm.id, "name": lm.name}
                for lm in locomotive_models_result.scalars().all()
            ],
            "fault_discovered_at": [
                {"id": fd.id, "name": fd.name}
                for fd in fault_discovery_places_result.scalars().all()
            ],
            "repair_types": [
                {
                    "id": rt.id,
                    "name": rt.name,
                    "auto_fill_strategy": rt.auto_fill_strategy,
                }
                for rt in repair_types_result.scalars().all()
            ],
            "equipment_owners": [
                {"id": eo.id, "name": eo.name}
                for eo in equipment_owners_result.scalars().all()
            ],
            "performed_by": [
                {"id": rp.id, "name": rp.name}
                for rp in repair_performers_result.scalars().all()
            ],
            "destinations": [
                {"id": dt.id, "name": dt.name}
                for dt in destination_types_result.scalars().all()
            ],
            "malfunctions": [
                {"id": m.id, "name": m.name}
                for m in malfunctions_result.scalars().all()
            ],
            "suppliers": [
                {"id": s.id, "name": s.name} for s in suppliers_result.scalars().all()
            ],
            "notification_summaries": [
                {"id": ns.id, "name": ns.name}
                for ns in notification_summaries_result.scalars().all()
            ],
            "response_summaries": [
                {"id": rs.id, "name": rs.name}
                for rs in response_summaries_result.scalars().all()
            ],
            "decision_summaries": [
                {"id": ds.id, "name": ds.name}
                for ds in decision_summaries_result.scalars().all()
            ],
        }

    @staticmethod
    async def get_filter_references(session: AsyncSession):
        """Получить только те справочники, которые нужны для фильтров"""
        (
            regional_centers_result,
            locomotive_models_result,
            suppliers_result,
            repair_types_result,
        ) = await asyncio.gather(
            session.execute(select(RegionalCenter)),
            session.execute(select(LocomotiveModel)),
            session.execute(select(Supplier)),
            session.execute(select(RepairType)),
        )

        return {
            "regional_centers": [
                {"id": rc.id, "name": rc.name}
                for rc in regional_centers_result.scalars().all()
            ],
            "locomotive_models": [
                {"id": lm.id, "name": lm.name}
                for lm in locomotive_models_result.scalars().all()
            ],
            "suppliers": [
                {"id": s.id, "name": s.name} for s in suppliers_result.scalars().all()
            ],
            "repair_types": [
                {
                    "id": rt.id,
                    "name": rt.name,
                    "auto_fill_strategy": rt.auto_fill_strategy,  # <-- Включаем стратегию
                }
                for rt in repair_types_result.scalars().all()
            ],
        }

    @staticmethod
    async def get_equipment_references(session: AsyncSession):
        """Получить оборудование для выпадающих списков"""
        equipment_stmt = select(Equipment).where(Equipment.parent_id == None)
        elements_stmt = select(Equipment).where(Equipment.parent_id != None)

        equipment_result, elements_result = await asyncio.gather(
            session.execute(equipment_stmt),
            session.execute(elements_stmt),
        )

        return {
            "components": [
                {"id": equip.id, "name": equip.name}
                for equip in equipment_result.scalars().all()
            ],
            "elements": [
                {"id": equip.id, "name": equip.name}
                for equip in elements_result.scalars().all()
            ],
        }
