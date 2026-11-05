from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from myapp.services import CaseValidationError
from myapp.services.user_access_service import lock_case_for_change
from myapp.models.warranty_work import WarrantyWork, NotificationSummary
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.schemas.warranty import WarrantyWorkUpdate
from myapp.database.transactional import transactional
from myapp.database.query_builders.query_case_builders import load_warranty_relations


class WarrantyService:
    _TRAIN_NOTIFICATION_NAMES = frozenset({
        "Командировать представителя", "Командировать представителя в депо",
        "Не требуется", "Негарантийный (по сроку)",
    })

    @staticmethod
    def filter_train_references(references):
        """Оставляет разрешённые поездные варианты без удаления справочников"""
        allowed_names = WarrantyService._TRAIN_NOTIFICATION_NAMES
        return {
            **references,
            "notification_summaries": [
                item
                for item in references.get("notification_summaries", [])
                if item["name"] in allowed_names
            ],
            "response_summaries": [
                item
                for item in references.get("response_summaries", [])
                if item["id"] not in (5, 12, 14)
            ],
            "decision_summaries": [
                item
                for item in references.get("decision_summaries", [])
                if item["id"] not in (2, 10)
            ],
        }

    @staticmethod
    async def validate_train_summaries(session, data):
        """Запрещает скрытые значения при любом сохранении поездной рекламации"""
        if data.response_summary_id in (5, 12, 14):
            raise CaseValidationError(
                "response_summary_id", "Этот ответ поставщика недоступен для поездов"
            )
        if data.decision_summary_id in (2, 10):
            raise CaseValidationError(
                "decision_summary_id", "Это решение недоступно для поездов"
            )
        if data.notification_summary_id is not None:
            item = await session.get(NotificationSummary, data.notification_summary_id)
            if item is None or item.notification_summary_name not in WarrantyService._TRAIN_NOTIFICATION_NAMES:
                raise CaseValidationError(
                    "notification_summary_id",
                    "Это содержание уведомления недоступно для поездов",
                )

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
        session: AsyncSession,
        case_id: int,
        warranty_data: WarrantyWorkUpdate,
        *,
        expected_revision: int | None = None,
        bump_revision: bool = True,
    ) -> WarrantyWork | None:
        """Обновляет рекламацию с проверкой версии при отдельном сохранении"""
        case = await lock_case_for_change(session, case_id)
        if bump_revision and expected_revision != case.revision:
            raise CaseValidationError(
                "revision", "Случай изменён другим пользователем. Обновите карточку."
            )
        if case.direction == "train":
            await WarrantyService.validate_train_summaries(session, warranty_data)
        if case.direction == "train" and any(
            getattr(warranty_data, field, None)
            for field in (
                "re_notification_number",
                "re_notification_date",
                "research_document",
                "research_status_id",
                "investigation_reason_id",
            )
        ):
            raise ValueError(
                "Повторное уведомление и акт исследования для поездов не используются"
            )
        warranty_work = await WarrantyService._get_warranty_work_with_relations(
            case_id, session
        )

        warranty_data.validate_dates(case.fault_date, warranty_work)

        if warranty_work is None:
            case = await session.get(RepairCaseEquipment, case_id)
            if case is None:
                raise ValueError("Случай не найден")
            await session.refresh(case, ["warranty_work"])
            warranty_work = WarrantyWork(case_id=case_id)
            case.warranty_work = warranty_work
            session.add(warranty_work)

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

        if bump_revision:
            case.revision += 1
        return warranty_work
