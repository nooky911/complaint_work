from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models.repair_case_equipment import RepairCaseEquipment
from models.warranty_work import WarrantyWork
from schemas.cases import CaseList
from schemas.filters import FilterOptionsResponse
from schemas.filters import CaseFilterParams
from database.query_builders.query_case_filters import (
    build_repair_case_conditions,
    build_warranty_work_conditions,
    status_expr
)


class CaseFilterService:
    """Сервис фильтрации с использованием функции БД"""
    @staticmethod
    async def filter_cases(session: AsyncSession, params: CaseFilterParams) -> list[CaseList]:

        # Выражение для статуса
        stmt = select(RepairCaseEquipment, status_expr)
        stmt = stmt.outerjoin(RepairCaseEquipment.warranty_work)

        # Базовый запрос с выборкой статуса
        stmt = (stmt.options(
                joinedload(RepairCaseEquipment.regional_center),
                joinedload(RepairCaseEquipment.locomotive_model),
                joinedload(RepairCaseEquipment.component_equipment),
                joinedload(RepairCaseEquipment.element_equipment),
                joinedload(RepairCaseEquipment.malfunction),
                joinedload(RepairCaseEquipment.repair_type),
                joinedload(RepairCaseEquipment.supplier),

                joinedload(RepairCaseEquipment.warranty_work).selectinload(WarrantyWork.notification_summary),
                joinedload(RepairCaseEquipment.warranty_work).selectinload(WarrantyWork.response_summary),
                joinedload(RepairCaseEquipment.warranty_work).selectinload(WarrantyWork.decision_summary),
            )
        )

        all_conditions = []

        #Сбор отфильтрованных парамеров
        all_conditions.extend(build_repair_case_conditions(params))
        all_conditions.extend(build_warranty_work_conditions(params))

        if all_conditions:
            stmt = stmt.where(and_(*all_conditions))

        stmt = stmt.offset(params.skip).limit(params.limit).order_by(RepairCaseEquipment.date_recorded.desc())

        result = await session.execute(stmt)
        rows = result.unique().all()

        cases = [CaseList.model_validate(case) for case, _ in rows]

        return cases


    @staticmethod
    async def get_filter_options(session: AsyncSession) -> FilterOptionsResponse:
        """Получение опций для фильтров (для выпадающих списков на фронте)"""
        from models.auxiliaries import RegionalCenter, LocomotiveModel, Supplier, RepairType
        from models.equipment_mulfunctions import Equipment, Malfunction

        # Запросы для всех справочников
        regional_centers_stmt = select(RegionalCenter)
        locomotive_models_stmt = select(LocomotiveModel)
        equipment_stmt = select(Equipment).where(Equipment.parent_id == None)
        malfunctions_stmt = select(Malfunction)
        suppliers_stmt = select(Supplier)
        repair_types_stmt = select(RepairType)

        regional_centers_result = await session.execute(regional_centers_stmt)
        locomotive_models_result = await session.execute(locomotive_models_stmt)
        equipment_result = await session.execute(equipment_stmt)
        malfunctions_result = await session.execute(malfunctions_stmt)
        suppliers_result = await session.execute(suppliers_stmt)
        repair_types_result = await session.execute(repair_types_stmt)

        data = {
            "regional_centers": [{"id": rc.id, "name": rc.regional_center_name} for rc in
                                 regional_centers_result.scalars().all()],
            "locomotive_models": [{"id": lm.id, "name": lm.locomotive_model_name} for lm in
                                  locomotive_models_result.scalars().all()],
            "components": [{"id": equip.id, "name": equip.equipment_name} for equip in
                           equipment_result.scalars().all()],
            "malfunctions": [{"id": m.id, "name": m.defect_name} for m in malfunctions_result.scalars().all()],
            "suppliers": [{"id": s.id, "name": s.supplier_name} for s in suppliers_result.scalars().all()],
            "repair_types": [{"id": rt.id, "name": rt.repair_types_name} for rt in repair_types_result.scalars().all()],
            "statuses": [
                "Ожидает уведомление поставщика",
                "Уведомление отправлено",
                "Ответ получен",
                "Решение принято",
                "Ожидает АВР",
                "Ожидает рекламационный акт",
                "Ожидает ответа поставщика",
                "Ожидает повторного уведомления поставщика",
                "Завершено"
            ]
        }

        return FilterOptionsResponse.model_validate(data)