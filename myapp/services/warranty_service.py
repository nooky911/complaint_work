from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from myapp.models.warranty_work import WarrantyWork
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.schemas.warranty import WarrantyWorkUpdate
from myapp.database.transactional import transactional
from myapp.database.query_builders.query_case_builders import load_warranty_relations


class WarrantyService:

    @staticmethod
    async def _get_warranty_work_with_relations(
        case_id: int, session: AsyncSession
    ) -> WarrantyWork | None:
        """Внутренний метод для получения WarrantyWork со связями"""
        stmt = (
            select(WarrantyWork)
            .options(*load_warranty_relations())
            .join(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
        )
        result = await session.execute(stmt)

        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_warranty_by_case(
        session: AsyncSession, case_id: int
    ) -> WarrantyWork | None:
        """Получение данных по рекл. работе"""
        return await WarrantyService._get_warranty_work_with_relations(case_id, session)

    @staticmethod
    @transactional
    async def update_warranty_work(
        session: AsyncSession, case_id: int, warranty_data: WarrantyWorkUpdate
    ) -> WarrantyWork | None:
        """Редактирование"""
        warranty_work = await WarrantyService._get_warranty_work_with_relations(
            case_id, session
        )

        if not warranty_work:
            return None

        # Валидация соответствия статуса исследования и причины исследования
        update_data = warranty_data.model_dump(exclude_unset=True)

        # Проверяем только если хотя бы одно из полей исследования присутствует в обновлении
        if (
            "research_status_id" in update_data
            or "investigation_reason_id" in update_data
        ):
            research_status_id = update_data.get(
                "research_status_id", warranty_work.research_status_id
            )
            reason_id = update_data.get(
                "investigation_reason_id", warranty_work.investigation_reason_id
            )

            # Если статус исследования указан, проверяем соответствие причины
            if research_status_id is not None:
                # Статусы 3, 5, 6 не должны иметь причины
                if research_status_id in [3, 5, 6] and reason_id is not None:
                    raise ValueError(
                        f"Для статуса исследования {research_status_id} нельзя указывать причину"
                    )

                # Статус 1 -> причины 1-5
                if (
                    research_status_id == 1
                    and reason_id is not None
                    and reason_id not in [1, 2, 3, 4, 5]
                ):
                    raise ValueError(
                        "Для статуса исследования 1 доступны только причины 1-5"
                    )

                # Статусы 2 и 4 -> причины 6-9
                if (
                    research_status_id in [2, 4]
                    and reason_id is not None
                    and reason_id not in [6, 7, 8, 9]
                ):
                    raise ValueError(
                        "Для статуса исследования 2 или 4 доступны только причины 6-9"
                    )

        # Обновление данных
        for field, value in update_data.items():
            setattr(warranty_work, field, value)

        return warranty_work
