from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from datetime import date
from typing import List

from models.repair_case_equipment import RepairCaseEquipment
from models.warranty_work import WarrantyWork
from schemas.cases import CaseList


class CaseFilterService:
    """Сервис фильтрации с использованием функции БД"""

    @staticmethod
    async def filter_cases(
            session,
            # Основные фильтры
            date_from: date | None = None,
            date_to: date | None = None,
            section_mask: int | None = None,
            locomotive_number: str | None = None,
            component_serial_number_old: str | None = None,
            element_serial_number_old: str | None = None,
            component_serial_number_new: str | None = None,
            element_serial_number_new: str | None = None,
            regional_center_id: int | None = None,
            locomotive_model_id: int | None = None,
            component_equipment_id: int | None = None,
            element_equipment_id: int | None = None,
            malfunction_id: int | None = None,
            repair_type_id: int | None = None,
            supplier_id: int | None = None,

            status: str | None = None,

            skip: int = 0,
            limit: int = 50
    ) -> List[CaseList]:

        # Выражение для статуса
        status_expr = func.calculate_case_status(
            WarrantyWork.notification_summary_id,
            WarrantyWork.response_summary_id,
            WarrantyWork.decision_summary_id,
            WarrantyWork.work_completion_act_number,
            WarrantyWork.claim_act_number,
            WarrantyWork.re_notification_number,
            WarrantyWork.re_notification_date,
            WarrantyWork.notification_date
        )

        # Базовый запрос с выборкой статуса
        stmt = (
            select(
                RepairCaseEquipment,
                status_expr.label('calculated_status')
            )
            .outerjoin(RepairCaseEquipment.warranty_work)
            .options(
                joinedload(RepairCaseEquipment.regional_center),
                joinedload(RepairCaseEquipment.locomotive_model),
                joinedload(RepairCaseEquipment.component_equipment),
                joinedload(RepairCaseEquipment.element_equipment),
                joinedload(RepairCaseEquipment.malfunction),
                joinedload(RepairCaseEquipment.repair_type),
                joinedload(RepairCaseEquipment.supplier),

                # warranty_work
                joinedload(RepairCaseEquipment.warranty_work)
                    .selectinload(WarrantyWork.notification_summary)
                    .selectinload(WarrantyWork.response_summary)
                    .selectinload(WarrantyWork.decision_summary),
            )
        )

        conditions = []

        # Фильтры по датам
        if date_from:
            conditions.append(RepairCaseEquipment.fault_date >= date_from)
        if date_to:
            conditions.append(RepairCaseEquipment.fault_date <= date_to)
        # По секции
        if section_mask is not None:
            conditions.append(RepairCaseEquipment.section_mask == section_mask)
        # Фильтры по строковым полям
        if locomotive_number:
            conditions.append(RepairCaseEquipment.locomotive_number.ilike(f"%{locomotive_number}%"))
        if component_serial_number_old:
            conditions.append(RepairCaseEquipment.component_serial_number_old.ilike(f"%{component_serial_number_old}%"))
        if element_serial_number_old:
            conditions.append(RepairCaseEquipment.element_serial_number_old.ilike(f"%{element_serial_number_old}%"))
        if component_serial_number_new:
            conditions.append(RepairCaseEquipment.component_serial_number_new.ilike(f"%{component_serial_number_new}%"))
        if element_serial_number_new:
            conditions.append(RepairCaseEquipment.element_serial_number_new.ilike(f"%{element_serial_number_new}%"))
        # Фильтры по ID
        if regional_center_id is not None:
            conditions.append(RepairCaseEquipment.regional_center_id == regional_center_id)
        if locomotive_model_id is not None:
            conditions.append(RepairCaseEquipment.locomotive_model_id == locomotive_model_id)
        if component_equipment_id is not None:
            conditions.append(RepairCaseEquipment.component_equipment_id == component_equipment_id)
        if element_equipment_id is not None:
            conditions.append(RepairCaseEquipment.element_equipment_id == element_equipment_id)
        if malfunction_id is not None:
            conditions.append(RepairCaseEquipment.malfunction_id == malfunction_id)
        if repair_type_id is not None:
            conditions.append(RepairCaseEquipment.repair_type_id == repair_type_id)
        if supplier_id is not None:
            conditions.append(RepairCaseEquipment.supplier_id == supplier_id)
        # Фильтр по статусу
        if status:
            conditions.append(status_expr == status)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.offset(skip).limit(limit).order_by(RepairCaseEquipment.date_recorded.desc())

        # Выполняем запрос и обрабатываем результаты
        result = await session.execute(stmt)
        rows = result.unique().all()

        cases = [
            CaseList.model_validate(case, context={'status': calculated_status})
            for case, calculated_status in rows
        ]

        return cases


    @staticmethod
    async def get_filter_options(session):
        """Получение опций для фильтров (для выпадающих списков на фронтенде)"""
        from models.auxiliaries import RegionalCenter, LocomotiveModel, Supplier, RepairType
        from models.equipment_mulfunctions import Equipment, Malfunction

        # Делаем запросы для всех справочников
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

        return {
            "regional_centers": [{"id": rc.id, "name": rc.name} for rc in regional_centers_result.scalars().all()],
            "locomotive_models": [{"id": lm.id, "name": lm.name} for lm in locomotive_models_result.scalars().all()],
            "components": [{"id": comp.id, "name": comp.name} for comp in equipment_result.scalars().all()],
            "malfunctions": [{"id": m.id, "name": m.name} for m in malfunctions_result.scalars().all()],
            "suppliers": [{"id": s.id, "name": s.name} for s in suppliers_result.scalars().all()],
            "repair_types": [{"id": rt.id, "name": rt.name} for rt in repair_types_result.scalars().all()],
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