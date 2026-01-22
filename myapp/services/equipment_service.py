from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.equipment_malfunctions import Equipment
from myapp.schemas.equipment import EquipmentWithPathResponse


class EquipmentService:

    @staticmethod
    async def get_equipment_by_level(
        session: AsyncSession, level: int, parent_id: int | None, query: str = ""
    ) -> list[EquipmentWithPathResponse]:
        """Получить оборудование для конкретного уровня иерархии"""
        conditions = []

        # 1. Логика фильтрации по родителю
        if level == 0:
            conditions.append(Equipment.parent_id.is_(None))
        else:
            if parent_id is not None:
                conditions.append(Equipment.parent_id == parent_id)
            else:
                return []

        # 2. Поиск
        if query:
            conditions.append(Equipment.equipment_name.ilike(f"%{query}%"))

        # 3. Выполнение запроса
        stmt = select(Equipment).where(*conditions).order_by(Equipment.equipment_name)
        result = await session.execute(stmt)
        equipment_list = result.scalars().all()

        # 4. Проверка наличия детей
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

        # 5. Ответ
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
        """Получить полную цепочку от корня до выбранного оборудования"""

        # 1. Находим все ID в цепочке, идя вверх
        current_id = equipment_id
        chain_ids = []

        while current_id:
            chain_ids.append(current_id)
            parent_stmt = select(Equipment.parent_id).where(Equipment.id == current_id)
            result = await session.execute(parent_stmt)
            parent_id = result.scalar_one_or_none()

            if parent_id is None or parent_id == current_id:
                break

            current_id = parent_id

        if not chain_ids:
            return []

        # 2. Получаем все объекты в цепочке одним запросом
        equipment_stmt = select(Equipment).where(Equipment.id.in_(chain_ids))
        result = await session.execute(equipment_stmt)
        equipment_list = result.scalars().all()

        # Создаем карту ID -> Объект
        equipment_map = {eq.id: eq for eq in equipment_list}

        # 3. Определяем уровень для каждого оборудования (рекурсивно)
        def calculate_level(item_id: int) -> int:
            """Вспомогательная функция для расчета уровня оборудования"""
            equipment_item = equipment_map.get(item_id)
            if not equipment_item:
                return 0
            if equipment_item.parent_id is None:
                return 0
            return calculate_level(equipment_item.parent_id) + 1

        # 4. Проверяем наличие детей для каждого оборудования
        all_equipment_ids = [eq.id for eq in equipment_map.values()]
        children_stmt = (
            select(Equipment.parent_id)
            .where(Equipment.parent_id.in_(all_equipment_ids))
            .distinct()
        )
        children_result = await session.execute(children_stmt)
        parents_with_children = {row[0] for row in children_result}

        # 5. Собираем цепочку в правильном порядке (от корня к выбранному)
        chain = []
        ordered_ids = list(reversed(chain_ids))

        for eq_id in ordered_ids:
            eq = equipment_map.get(eq_id)
            if eq:
                level = calculate_level(eq.id)
                has_children = eq_id in parents_with_children

                chain.append(
                    EquipmentWithPathResponse(
                        id=eq.id,
                        name=eq.equipment_name,
                        level=level,
                        has_children=has_children,
                        parent_id=eq.parent_id,
                        supplier_id=eq.supplier_id,
                    )
                )

        return chain

    @staticmethod
    async def get_equipment_with_level(
        session: AsyncSession, equipment_id: int
    ) -> tuple[Equipment, int] | None:
        """Получить оборудование с его реальным уровнем в иерархии"""
        chain = await EquipmentService.get_equipment_chain(session, equipment_id)

        if not chain:
            return None

        # Находим последний элемент (выбранное оборудование)
        last_item = chain[-1]

        # Получаем полный объект Equipment
        equipment = await session.get(Equipment, equipment_id)
        if not equipment:
            return None

        return equipment, last_item.level

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
    async def get_all_equipment_flat(
        session: AsyncSession,
    ) -> list[EquipmentWithPathResponse]:
        """Получить ВСЕ оборудование плоским списком"""
        stmt = select(Equipment)
        result = await session.execute(stmt)
        equipment_list = result.scalars().all()

        return [EquipmentWithPathResponse.model_validate(eq) for eq in equipment_list]
