import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.schemas.cases import CaseCreate, CaseUpdate
from myapp.database.query_builders.query_case_builders import load_detail_relations
from myapp.database.transactional import transactional
from myapp.services.equipment_service import EquipmentService
from myapp.services.warranty_service import WarrantyService
from myapp.services.case_status_service import CaseStatusService
from myapp.services.storage_service import StorageService


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

        # 1. Разделяем данные: извлекаем вложенную модель warranty_work
        case_creation_data = case_data.model_dump(exclude={"warranty_work"})
        warranty_work_data = (
            case_data.warranty_work.model_dump(exclude_unset=True)
            if case_data.warranty_work
            else {}
        )

        # 2. Создаем RepairCaseEquipment только с его собственными полями
        case = RepairCaseEquipment(**case_creation_data)
        case.date_recorded = datetime.now()
        case.user_id = user_id

        # 3. Создаем WarrantyWork и привязываем его как ORM-объект
        new_warranty_work = WarrantyWork(**warranty_work_data)
        case.warranty_work = new_warranty_work

        # 4. Пересчет supplier_id
        if case.component_equipment_id:
            supplier_id = await EquipmentService.find_supplier_in_parents(
                session, case.component_equipment_id
            )
            case.supplier_id = supplier_id

        session.add(case)
        await session.flush()

        # 5. Получаем объект со всеми связями и вычисленным статусом
        created_case = await CaseService._get_case_with_relations(session, case.id)
        return created_case

    @staticmethod
    @transactional
    async def update_case(
        session: AsyncSession, case_id: int, case_data: CaseUpdate
    ) -> RepairCaseEquipment | None:
        """Обновление случая, включая WarrantyWork, и автоматическое переопределение supplier_id"""
        case: RepairCaseEquipment | None = await session.get(
            RepairCaseEquipment, case_id
        )
        if not case:
            return None

        update_data = case_data.model_dump(
            exclude_unset=True, exclude={"warranty_work"}
        )

        component_changed = "component_equipment_id" in update_data
        element_changed = "element_equipment_id" in update_data

        # ЛОГИКА ОПРЕДЕЛЕНИЯ ПОСТАВЩИКА:
        # 1. Если изменилось оборудование
        if component_changed or element_changed:
            equipment_id_for_search = None

            # Приоритет: component_equipment_id > element_equipment_id
            if component_changed:
                equipment_id_for_search = update_data.get("component_equipment_id")
            elif element_changed:
                equipment_id_for_search = update_data.get("element_equipment_id")

            # Если equipment_id передан как null (сброс выбора), то поставщик = null
            if equipment_id_for_search is None:
                update_data["supplier_id"] = None
            # Если equipment_id передан, ищем поставщика
            else:
                found_supplier_id = await EquipmentService.find_supplier_in_parents(
                    session, equipment_id_for_search
                )
                update_data["supplier_id"] = found_supplier_id
        # 2. Если оборудование не менялось, НЕ трогаем supplier_id
        else:
            # Не добавляем supplier_id в update_data, чтобы не менять его
            pass

        # Обновляем поля
        for field, value in update_data.items():
            setattr(case, field, value)

        await session.flush()

        # Обновление WarrantyWork
        if case_data.warranty_work:
            await WarrantyService.update_warranty_work(
                session, case_id, case_data.warranty_work
            )

        return await CaseService._get_case_with_relations(session, case.id)

    @staticmethod
    @transactional
    async def delete_case(session: AsyncSession, case_id: int) -> int:
        """Удаление случая, его документов и физических файлов"""

        case = await CaseService.get_case(session, case_id)

        if not case:
            return 0

        if case.files:
            for file_rec in case.files:
                full_path = StorageService.get_full_path(file_rec)
                try:
                    await asyncio.to_thread(full_path.unlink, missing_ok=True)
                except Exception as e:
                    print(f"Ошибка при удалении файла {full_path}: {e}")

        await session.delete(case)

        return 1
