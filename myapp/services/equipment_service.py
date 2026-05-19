from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from myapp.database.transactional import transactional
from myapp.models import RepairCaseEquipment
from myapp.models.equipment_malfunctions import (
    Equipment,
    Malfunction,
    EquipmentMalfunction,
)
from myapp.models.auxiliaries import Supplier
from myapp.schemas.equipment import (
    EquipmentWithPathResponse,
    EquipmentCreate,
    EquipmentUpdate,
    SupplierUpdate,
    MalfunctionUpdate,
)
from myapp.services.cache_service import cache


class EquipmentService:

    @staticmethod
    async def _get_has_children_map(
        session: AsyncSession, equipment_ids: list[int]
    ) -> dict[int, bool]:
        """Универсальная проверка наличия дочерних элементов для списка ID за один запрос"""
        if not equipment_ids:
            return {}

        stmt = (
            select(Equipment.parent_id)
            .where(Equipment.parent_id.in_(equipment_ids))
            .distinct()
        )
        result = await session.execute(stmt)
        parents_with_children = {row[0] for row in result}

        return {eq_id: (eq_id in parents_with_children) for eq_id in equipment_ids}

    @staticmethod
    @transactional
    async def get_or_create_supplier(
        session: AsyncSession, name: str
    ) -> tuple[Supplier, bool]:
        """Найти поставщика по имени или создать нового, если его нет"""

        stmt = select(Supplier).where(Supplier.supplier_name == name)
        supplier = (await session.execute(stmt)).scalar_one_or_none()

        was_created = False
        if not supplier:
            supplier = Supplier(supplier_name=name)
            session.add(supplier)
            await session.flush()
            was_created = True
            await cache.clear()

        return supplier, was_created

    @staticmethod
    @transactional
    async def update_supplier(
        session: AsyncSession, supplier_id: int, data: SupplierUpdate
    ) -> Supplier:
        """Редактирует имя Поставщика"""

        supplier: Supplier | None = await session.get(Supplier, supplier_id)

        if not supplier:
            raise ValueError(f"Поставщик с ID {supplier_id} не найден")

        if data.supplier_name:
            stmt = select(Supplier).where(Supplier.supplier_name == data.supplier_name)
            existing = (await session.execute(stmt)).scalar_one_or_none()

            if existing and existing.id != supplier_id:
                raise ValueError(
                    f"Поставщик '{data.supplier_name}' уже есть в справочнике"
                )

            supplier.supplier_name = data.supplier_name

        await session.flush()
        await cache.clear()

        return supplier

    @staticmethod
    @transactional
    async def delete_supplier(session: AsyncSession, supplier_id: int) -> bool:
        """Удалить поставщика"""
        stmt = select(Equipment.id).where(Equipment.supplier_id == supplier_id).limit(1)
        if (await session.execute(stmt)).scalar_one_or_none():
            raise ValueError("Нельзя удалить: поставщик закреплен за оборудованием.")

        result = await session.execute(
            delete(Supplier).where(Supplier.id == supplier_id)
        )
        await session.flush()

        if result.rowcount > 0:
            await cache.clear()

        return result.rowcount > 0

    @staticmethod
    async def find_supplier_in_parents(
        session: AsyncSession, equipment_id: int
    ) -> int | None:
        """Рекурсивно найти supplier_id в родительском оборудовании"""
        current_id = equipment_id

        while current_id:
            equipment: Equipment | None = await session.get(Equipment, current_id)
            if not equipment:
                break

            if equipment.supplier_id is not None:
                return equipment.supplier_id

            current_id = equipment.parent_id

        return None

    @staticmethod
    async def resolve_supplier(
        session: AsyncSession,
        equipment_id: int | None,
        locomotive_number: str | None = None,
        locomotive_model_id: int | None = None,
    ) -> int | None:
        """Правила определения определённых поставщиков"""

        if not equipment_id:
            return None

        base_supplier_id = await EquipmentService.find_supplier_in_parents(
            session, equipment_id
        )

        if base_supplier_id is None:
            return None

        # Номера локомотивов для поставщика НПК СО
        loco_numbers = ("730", "731", "732", "733", "734")

        # Поставщики (13: МТЗ Трансмаш, 26: Горизонт, 40: НПО САУТ, 55: Тяговые компоненты)
        replace_supp_npk = (13, 26, 40, 55)
        replace_supp_3es8 = (26, 40)

        # Переназначение на НПК СО (ID 38)
        if base_supplier_id in replace_supp_npk:
            if (
                locomotive_number in loco_numbers
                or locomotive_model_id == 2
                or (locomotive_model_id in (3, 7) and locomotive_number == "1")
            ):
                return 38

        # Переназначение на ООО «Тяговые компоненты» (ID 55)
        if locomotive_model_id in (3, 7) and base_supplier_id in replace_supp_3es8:
            return 55

        return base_supplier_id

    @staticmethod
    @transactional
    async def get_or_create_malfunction(
        session: AsyncSession, name: str
    ) -> Malfunction:
        """Найти или создать неисправность"""

        stmt = select(Malfunction).where(Malfunction.defect_name == name)
        malf = (await session.execute(stmt)).scalar_one_or_none()
        if not malf:
            malf = Malfunction(defect_name=name)
            session.add(malf)
            await session.flush()
            await cache.clear()
        return malf

    @staticmethod
    @transactional
    async def update_malfunction(
        session: AsyncSession, malf_id: int, data: MalfunctionUpdate
    ) -> Malfunction:
        """Редактирует имя неисправности"""

        malfunction: Malfunction | None = await session.get(Malfunction, malf_id)

        if not malfunction:
            raise ValueError(f"Неисправность с ID {malf_id} не найдена")

        if data.defect_name:
            stmt = select(Malfunction).where(
                Malfunction.defect_name == data.defect_name
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()

            if existing and existing.id != malf_id:
                raise ValueError(
                    f"Неисправность '{data.defect_name}' уже есть в справочнике"
                )

            malfunction.defect_name = data.defect_name

        await session.flush()
        await cache.clear()

        return malfunction

    @staticmethod
    @transactional
    async def delete_malfunction(session: AsyncSession, malf_id: int) -> bool:
        """Удалить неисправность"""

        case_stmt = (
            select(RepairCaseEquipment.id)
            .where(RepairCaseEquipment.malfunction_id == malf_id)
            .limit(1)
        )
        case_exists = (await session.execute(case_stmt)).scalar_one_or_none()

        if case_exists:
            raise ValueError(
                "Нельзя удалить неисправность: она уже зафиксирована в случаях ремонта."
            )

        link_stmt = delete(EquipmentMalfunction).where(
            EquipmentMalfunction.malfunction_id == malf_id
        )
        await session.execute(link_stmt)

        malf_stmt = delete(Malfunction).where(Malfunction.id == malf_id)
        result = await session.execute(malf_stmt)

        await session.flush()

        if result.rowcount > 0:
            await cache.clear()

        return result.rowcount > 0

    @staticmethod
    async def _get_existing_equipment(
        session: AsyncSession, name: str, parent_id: int | None
    ):
        """Проверка на наличие оборудования"""
        stmt = select(Equipment).where(
            Equipment.equipment_name == name, Equipment.parent_id == parent_id
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_all_equipment_flat(
        session: AsyncSession,
    ) -> list[EquipmentWithPathResponse]:
        """Получить ВСЕ оборудование плоским списком"""
        stmt = select(Equipment)
        result = await session.execute(stmt)
        equipment_list = result.scalars().all()

        if not equipment_list:
            return []

        ids = [eq.id for eq in equipment_list]
        children_map = await EquipmentService._get_has_children_map(session, ids)

        return [
            EquipmentWithPathResponse(
                id=eq.id,
                name=eq.equipment_name,
                parent_id=eq.parent_id,
                supplier_id=eq.supplier_id,
                has_children=children_map.get(eq.id, False),
                level=None,
            )
            for eq in equipment_list
        ]

    @staticmethod
    async def get_equipment_by_level(
        session: AsyncSession, level: int, parent_id: int | None, query: str = ""
    ) -> list[EquipmentWithPathResponse]:
        """Получить оборудование для конкретного уровня иерархии"""
        conditions = []

        # Логика фильтрации по родителю
        if level == 0:
            conditions.append(Equipment.parent_id.is_(None))
        else:
            if parent_id is not None:
                conditions.append(Equipment.parent_id == parent_id)
            else:
                return []

        # Поиск
        if query:
            conditions.append(Equipment.equipment_name.ilike(f"%{query}%"))

        # Выполнение запроса
        stmt = select(Equipment).where(*conditions).order_by(Equipment.equipment_name)
        result = await session.execute(stmt)
        equipment_list = result.scalars().all()

        # Проверка наличия детей
        equipment_ids = [eq.id for eq in equipment_list]
        has_children_map = {}

        if equipment_ids:
            children_stmt = (
                select(Equipment.parent_id)
                .where(Equipment.parent_id.in_(equipment_ids))
                .distinct()
            )
            children_result = await session.execute(children_stmt)
            parents_with_children = {row[0] for row in children_result}
            has_children_map = {
                eq_id: eq_id in parents_with_children for eq_id in equipment_ids
            }

        return [
            EquipmentWithPathResponse(
                id=equipment.id,
                name=equipment.equipment_name,
                level=level,
                has_children=has_children_map.get(equipment.id, False),
                parent_id=equipment.parent_id,
                supplier_id=equipment.supplier_id,
            )
            for equipment in equipment_list
        ]

    @staticmethod
    async def get_equipment_chain(
        session: AsyncSession, equipment_id: int
    ) -> list[EquipmentWithPathResponse]:
        """Получить цепочку от корня до выбранного оборудования"""

        nodes = []
        current_id = equipment_id

        while current_id:
            eq = await session.get(Equipment, current_id)
            if not eq:
                break
            nodes.append(eq)
            current_id = eq.parent_id

            if len(nodes) > 10:
                break

        if not nodes:
            return []

        nodes.reverse()

        # Проверка детей для цепочки
        ids = [n.id for n in nodes]
        children_map = await EquipmentService._get_has_children_map(session, ids)

        return [
            EquipmentWithPathResponse(
                id=eq.id,
                name=eq.equipment_name,
                level=idx,
                has_children=children_map.get(eq.id, False),
                parent_id=eq.parent_id,
                supplier_id=eq.supplier_id,
            )
            for idx, eq in enumerate(nodes)
        ]

    @staticmethod
    async def get_equipment_with_level(
        session: AsyncSession, equipment_id: int
    ) -> tuple[Equipment, int] | None:
        """Получить оборудование с его реальным уровнем в иерархии"""

        chain = await EquipmentService.get_equipment_chain(session, equipment_id)

        if not chain:
            return None

        last_item = chain[-1]

        equipment: Equipment | None = await session.get(Equipment, equipment_id)
        if not equipment:
            return None

        return equipment, last_item.level

    @staticmethod
    @transactional
    async def create_equipment(
        session: AsyncSession, data: EquipmentCreate
    ) -> Equipment:
        """Создать оборудование с привязкой к неисправности и Поставщику"""

        existing = await EquipmentService._get_existing_equipment(
            session, data.equipment_name, data.parent_id
        )
        if existing:
            raise ValueError(f"Оборудование '{data.equipment_name}' уже существует")

        target_supplier_id = data.supplier_id

        if data.new_supplier_name:
            supp = await EquipmentService.get_or_create_supplier(
                session, data.new_supplier_name
            )
            target_supplier_id = supp.id

        new_eq = Equipment(
            equipment_name=data.equipment_name,
            parent_id=data.parent_id,
            supplier_id=target_supplier_id,
        )
        session.add(new_eq)
        await session.flush()

        all_malf_ids = list(data.malfunction_ids or [])

        if data.new_malfunctions:
            for name in data.new_malfunctions:
                m = await EquipmentService.get_or_create_malfunction(session, name)
                all_malf_ids.append(m.id)

        if all_malf_ids:
            await EquipmentService._attach_malfunctions_by_ids(
                session, new_eq.id, all_malf_ids
            )

        stmt = (
            select(Equipment)
            .options(selectinload(Equipment.malfunctions))
            .where(Equipment.id == new_eq.id)
        )
        result = await session.execute(stmt)

        await cache.clear()

        return result.scalar_one()

    @staticmethod
    @transactional
    async def update_equipment(
        session: AsyncSession, eq_id: int, data: EquipmentUpdate
    ) -> Equipment:
        """Обновления оборудования (имя или/и поставщик)"""

        equipment: Equipment | None = await session.get(Equipment, eq_id)

        if not equipment:
            raise ValueError(f"Оборудование с ID {eq_id} не найдено")

        if data.equipment_name:
            existing = await EquipmentService._get_existing_equipment(
                session, data.equipment_name, equipment.parent_id
            )
            if existing and existing.id != eq_id:
                raise ValueError(f"Оборудование '{data.equipment_name}' уже существует")

            equipment.equipment_name = data.equipment_name

        if data.supplier_id is not None:
            equipment.supplier_id = data.supplier_id

        await session.flush()
        await session.refresh(equipment, ["malfunctions"])
        await cache.clear()

        return equipment

    @staticmethod
    @transactional
    async def delete_equipment(session: AsyncSession, eq_id: int) -> bool:
        """Удалить оборудование"""

        child_stmt = select(Equipment.id).where(Equipment.parent_id == eq_id).limit(1)
        if (await session.execute(child_stmt)).scalar_one_or_none():
            raise ValueError("Сначала удалите дочернее оборудование.")

        case_stmt = (
            select(RepairCaseEquipment.id)
            .where(
                (RepairCaseEquipment.component_equipment_id == eq_id)
                | (RepairCaseEquipment.element_equipment_id == eq_id)
                | (RepairCaseEquipment.new_component_equipment_id == eq_id)
                | (RepairCaseEquipment.new_element_equipment_id == eq_id)
            )
            .limit(5)
        )

        cases = (await session.execute(case_stmt)).scalars().all()
        if cases:
            raise ValueError(
                f"Используется в ремонтах ID: {', '.join(map(str, cases))}"
            )

        await session.execute(
            delete(EquipmentMalfunction).where(
                EquipmentMalfunction.equipment_id == eq_id
            )
        )
        result = await session.execute(delete(Equipment).where(Equipment.id == eq_id))
        await session.flush()

        if result.rowcount > 0:
            await cache.clear()

        return result.rowcount > 0

    @staticmethod
    async def _attach_malfunctions_by_ids(
        session: AsyncSession, eq_id: int, malf_ids: list[int]
    ):
        """Атомарная привязка списка ID к оборудованию с проверкой на дубли связей"""
        for m_id in malf_ids:
            exists = await session.get(EquipmentMalfunction, (eq_id, m_id))
            if not exists:
                session.add(
                    EquipmentMalfunction(equipment_id=eq_id, malfunction_id=m_id)
                )

    @staticmethod
    @transactional
    async def add_malfunctions_to_equipment(
        session: AsyncSession,
        eq_id: int,
        malf_ids: list[int] = None,
        new_names: list[str] = None,
    ) -> list[Malfunction]:
        """Привязка к имеющемуся оборудованию и возврат полного списка неисправностей"""

        if malf_ids:
            await EquipmentService._attach_malfunctions_by_ids(session, eq_id, malf_ids)

        if new_names:
            for name in new_names:
                malf = await EquipmentService.get_or_create_malfunction(session, name)
                await EquipmentService._attach_malfunctions_by_ids(
                    session, eq_id, [malf.id]
                )

        stmt = (
            select(Malfunction)
            .join(EquipmentMalfunction)
            .where(EquipmentMalfunction.equipment_id == eq_id)
        )
        result = await session.execute(stmt)

        await cache.clear()

        return list(result.scalars().all())

    @staticmethod
    @transactional
    async def detach_malfunction(
        session: AsyncSession, eq_id: int, malf_id: int
    ) -> bool:
        """Удалить связь между оборудованием и неисправностью"""

        stmt = delete(EquipmentMalfunction).where(
            EquipmentMalfunction.equipment_id == eq_id,
            EquipmentMalfunction.malfunction_id == malf_id,
        )

        result = await session.execute(stmt)
        await session.flush()

        if result.rowcount > 0:
            await cache.clear()

        return result.rowcount > 0
