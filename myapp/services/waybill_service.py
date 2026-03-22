from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from myapp.models.waybill_docs import WaybillDoc
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.schemas.waybill import WaybillDocUpdate
from myapp.database.transactional import transactional
from myapp.database.query_builders.query_case_builders import load_waybill_relations


class WaybillService:

    @staticmethod
    async def _get_waybill_doc_with_relations(
        case_id: int, session: AsyncSession
    ) -> WaybillDoc | None:
        """Внутренний метод для получения WaybillDoc со связями"""

        stmt = (
            select(WaybillDoc)
            .options(*load_waybill_relations())
            .join(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
        )
        result = await session.execute(stmt)

        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_waybill_doc_by_case(
        session: AsyncSession,
        case_id: int,
    ) -> WaybillDoc | None:
        """Получение данных по ТТН"""
        return await WaybillService._get_waybill_doc_with_relations(case_id, session)

    @staticmethod
    @transactional
    async def update_waybill_doc(
        session: AsyncSession, case_id: int, waybill_data: WaybillDocUpdate
    ) -> WaybillDoc | None:
        """Редактирование данных ТТН"""

        waybill_doc = await WaybillService._get_waybill_doc_with_relations(
            case_id, session
        )

        if not waybill_doc:
            update_data = waybill_data.model_dump(exclude_unset=True)
            new_waybill_doc = WaybillDoc(**update_data, case_id=case_id)
            session.add(new_waybill_doc)
            return new_waybill_doc

        update_data = waybill_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(waybill_doc, field, value)

        return waybill_doc
