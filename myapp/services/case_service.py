import asyncio

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime

from myapp.models import WaybillDoc
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.schemas.cases import CaseCreate, CaseUpdate
from myapp.database.query_builders.query_case_builders import load_detail_relations
from myapp.database.transactional import transactional
from myapp.services.equipment_service import EquipmentService
from myapp.services.warranty_service import WarrantyService
from myapp.services.case_status_service import CaseStatusService
from myapp.services.storage_service import StorageService
from myapp.services.waybill_service import WaybillService


class CaseService:

    @staticmethod
    async def _get_case_with_relations(
        session: AsyncSession, case_id: int
    ) -> RepairCaseEquipment | None:
        """Внутренний метод для загрузки случая со всеми связями"""
        return await CaseStatusService.get_case_with_status(
            session, case_id, load_detail_relations
        )

    @staticmethod
    async def get_case(
        session: AsyncSession, case_id: int
    ) -> RepairCaseEquipment | None:
        """Получение подробного случая"""
        return await CaseService._get_case_with_relations(session, case_id)

    @staticmethod
    @transactional
    async def create_case(
        session: AsyncSession,
        case_data: CaseCreate,
        user_id: int,
    ) -> RepairCaseEquipment:
        """Создание случая"""

        # Проверка на точный дубликат перед созданием
        existing_case = await session.execute(
            select(RepairCaseEquipment).where(
                RepairCaseEquipment.fault_date == case_data.fault_date,
                RepairCaseEquipment.locomotive_number == case_data.locomotive_number,
                RepairCaseEquipment.component_equipment_id
                == case_data.component_equipment_id,
                RepairCaseEquipment.malfunction_id == case_data.malfunction_id,
                or_(
                    RepairCaseEquipment.mileage == case_data.mileage,
                    RepairCaseEquipment.mileage.is_(None) & (case_data.mileage is None),
                ),
            )
        )
        if existing_case.scalar_one_or_none():
            raise ValueError("Случай уже существует")

        # Разделение данных
        case_creation_data = case_data.model_dump(
            exclude={"warranty_work", "user_id", "waybill_doc"}
        )
        warranty_work_data = (
            case_data.warranty_work.model_dump(exclude_unset=True)
            if case_data.warranty_work
            else {}
        )
        waybill_doc_data = (
            case_data.waybill_doc.model_dump(exclude_unset=True)
            if case_data.waybill_doc
            else {}
        )

        # Создание RepairCaseEquipment только с его собственными полями
        case = RepairCaseEquipment(**case_creation_data)
        case.date_recorded = datetime.now()
        case.user_id = user_id

        # Создание WarrantyWork и привязывание как ORM-объект
        new_warranty_work = WarrantyWork(**warranty_work_data)
        case.warranty_work = new_warranty_work

        # Создание WaybillsDoc и привязывание как ORM-объект
        new_waybill_doc = WaybillDoc(**waybill_doc_data)
        case.waybill_doc = new_waybill_doc

        # Пересчет supplier_id
        start_eq_id = case.element_equipment_id or case.component_equipment_id
        case.supplier_id = await EquipmentService.resolve_supplier(
            session,
            equipment_id=start_eq_id,
            locomotive_number=case.locomotive_number,
            locomotive_model_id=case.locomotive_model_id,
        )

        session.add(case)
        await session.flush()

        # Получаем объект со всеми связями и вычисленным статусом
        created_case = await CaseService._get_case_with_relations(session, case.id)
        return created_case

    @staticmethod
    @transactional
    async def update_case(
        session: AsyncSession, case_id: int, case_data: CaseUpdate
    ) -> RepairCaseEquipment | None:
        """Обновление случая и автоматическое переопределение supplier_id"""
        case: RepairCaseEquipment | None = await session.get(
            RepairCaseEquipment, case_id
        )
        if not case:
            return None

        update_data = case_data.model_dump(
            exclude_unset=True, exclude={"warranty_work", "waybill_doc"}
        )

        eq_changed = "component_equipment_id" in update_data
        el_changed = "element_equipment_id" in update_data
        loco_num_changed = "locomotive_number" in update_data
        loco_model_changed = "locomotive_model_id" in update_data

        # ЛОГИКА ОПРЕДЕЛЕНИЯ ПОСТАВЩИКА:
        if eq_changed or el_changed or loco_num_changed or loco_model_changed:

            # Определяем актуальные ID оборудования (новое из update_data или старое из базы)
            current_el_id = update_data.get(
                "element_equipment_id", case.element_equipment_id
            )
            current_comp_id = update_data.get(
                "component_equipment_id", case.component_equipment_id
            )

            # Выбираем точку старта для поиска (Элемент важнее компонента)
            target_id = current_el_id or current_comp_id

            if target_id is None:
                update_data["supplier_id"] = None
            else:
                # Вызываем наш "умный" метод с проверкой исключений
                update_data["supplier_id"] = await EquipmentService.resolve_supplier(
                    session,
                    equipment_id=target_id,
                    locomotive_number=update_data.get(
                        "locomotive_number", case.locomotive_number
                    ),
                    locomotive_model_id=update_data.get(
                        "locomotive_model_id", case.locomotive_model_id
                    ),
                )

        # Обновляем поля
        for field, value in update_data.items():
            setattr(case, field, value)

        await session.flush()

        # Обновление WarrantyWork
        if case_data.warranty_work:
            await WarrantyService.update_warranty_work(
                session, case_id, case_data.warranty_work
            )

        # Обновление WaybillDoc
        if case_data.waybill_doc:
            await WaybillService.update_waybill_doc(
                session, case_id, case_data.waybill_doc
            )

        return await CaseService._get_case_with_relations(session, case.id)

    @staticmethod
    @transactional
    async def delete_case(session: AsyncSession, case_id: int) -> int:
        """Удаление случая со всеми его данными"""
        stmt = (
            select(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
            .options(selectinload(RepairCaseEquipment.files))
        )
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            return 1

        if case.files:
            for file_rec in case.files:
                full_path = StorageService.get_full_path(file_rec)
                try:
                    await asyncio.to_thread(full_path.unlink, missing_ok=True)
                except Exception as e:
                    print(f"Ошибка удаления файла {full_path}: {e}")

        await session.delete(case)

        return 1
