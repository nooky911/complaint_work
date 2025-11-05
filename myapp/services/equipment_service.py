from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from myapp.models.equipment_malfunctions import Equipment
from myapp.schemas.equipment import EquipmentWithPathResponse


class EquipmentService:

    @staticmethod
    async def get_equipment_by_level(
        session: AsyncSession, level: int, parent_id: int | None, query: str = ""
    ) -> list[EquipmentWithPathResponse]:
        """Получить оборудование для конкретного уровня иерархии, включая проверку уровня родителя"""
        conditions = []

        # 1. Логика фильтрации по родителю и проверка уровня
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
                supplier_id=equipment.supplier_id,
            )
            for equipment in equipment_list
        ]

    @staticmethod
    async def get_equipment_chain(
        session: AsyncSession, equipment_id: int
    ) -> list[EquipmentWithPathResponse]:
        """Получить полную цепочку от корня до выбранного оборудования"""

        # 1. Находим все ID в цепочке, идя вверх.
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

        # 2. Получаем все объекты в цепочке одним запросом (Batching)
        equipment_stmt = select(Equipment).where(Equipment.id.in_(chain_ids))
        result = await session.execute(equipment_stmt)
        equipment_list = result.scalars().all()

        # Создаем карту ID -> Объект
        equipment_map = {eq.id: eq for eq in equipment_list}

        # 3. Собираем цепочку в правильном порядке (от корня к выбранному)
        chain = []
        # Инвертируем ID, чтобы идти от корня к выбранному элементу
        ordered_ids = list(reversed(chain_ids))

        for index, eq_id in enumerate(ordered_ids):
            equipment = equipment_map.get(eq_id)
            if equipment:
                chain.append(
                    EquipmentWithPathResponse(
                        id=equipment.id,
                        name=equipment.equipment_name,
                        level=index,
                        has_children=False,
                        supplier_id=equipment.supplier_id,
                    )
                )

        return chain

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
