from datetime import datetime, timezone
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from myapp.database.query_builders.query_case_builders import load_detail_relations
from myapp.database.transactional import transactional
from myapp.constants.case_lock import is_case_lock_active
from myapp.models import WaybillDoc
from myapp.models.auxiliaries import LocomotiveNumberException
from myapp.models.product_passports import CasePassportLink, ProductPassport
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.user import User
from myapp.models.warranty_work import WarrantyWork
from myapp.schemas.cases import CaseCreate, CaseUpdate
from myapp.services import CaseValidationError
from myapp.services.case_status_service import CaseStatusService
from myapp.services.equipment_service import EquipmentService
from myapp.services.files.file_management_service import FileManagementService
from myapp.services.omega_services.passport_case_service import PassportCaseService
from myapp.services.omega_services.product_passport_service import (
    ProductPassportService,
)
from myapp.services.warranty_service import WarrantyService
from myapp.services.waybill_service import WaybillService


class CaseService:
    """Создание, изменение и удаление случаев"""

    @staticmethod
    async def _prepare_locomotive(
        session: AsyncSession, data: dict, case: RepairCaseEquipment | None = None
    ) -> None:
        """Проверяет модель, номер и секции локомотива"""
        identity_fields = (
            "locomotive_model_id",
            "locomotive_number",
            "section_mask",
            "passport_id",
        )
        if case is not None and case.locomotive_identity_locked:
            for field in identity_fields:
                if field in data and data[field] != getattr(case, field):
                    raise CaseValidationError(
                        field,
                        "Модель, номер и секции этого архивного случая изменять нельзя",
                    )
            return
        if case is not None and not any(field in data for field in identity_fields):
            return

        passport: ProductPassport | None = None
        if data.get("passport_id") is not None:
            passport = await session.get(ProductPassport, data["passport_id"])
            if passport is None:
                raise CaseValidationError("passport_id", "Выбранный паспорт не найден")
            for field, value in (
                ("locomotive_model_id", passport.locomotive_model_id),
                ("locomotive_number", passport.product_number),
            ):
                if field in data and data[field] is not None and data[field] != value:
                    raise CaseValidationError(
                        field, "Модель или номер не соответствует выбранному паспорту"
                    )
            model_id, number = passport.locomotive_model_id, passport.product_number
        else:
            model_id = data.get(
                "locomotive_model_id", getattr(case, "locomotive_model_id", None)
            )
            number = data.get(
                "locomotive_number", getattr(case, "locomotive_number", None)
            )
            if model_id is None or not isinstance(number, str) or not number.strip():
                raise CaseValidationError(
                    "locomotive_number", "Выберите модель и номер локомотива"
                )
            number = number.strip()

        exception = await session.get(LocomotiveNumberException, (model_id, number))
        if exception is not None:
            if passport is not None:
                raise CaseValidationError(
                    "passport_id", "Этот локомотив используется без привязки к паспорту"
                )
            allowed_mask = exception.section_mask
        else:
            if passport is None:
                passport = await session.scalar(
                    select(ProductPassport).where(
                        ProductPassport.locomotive_model_id == model_id,
                        ProductPassport.product_number == number,
                    )
                )
            if passport is None:
                raise CaseValidationError(
                    "locomotive_number",
                    "Номер недоступен для этой модели: нужен паспорт или разрешённое исключение",
                )
            masks = await ProductPassportService.get_section_masks(
                session, [passport.id]
            )
            allowed_mask = masks.get(passport.id, 0)
            if not allowed_mask:
                raise CaseValidationError(
                    "section_mask", "В паспорте не удалось определить доступные секции"
                )

        mask = data.get("section_mask", getattr(case, "section_mask", None))
        if type(mask) is not int or mask <= 0 or mask & ~allowed_mask:
            raise CaseValidationError(
                "section_mask", "Выбранные секции отсутствуют у этого локомотива"
            )
        data.update(
            locomotive_model_id=model_id,
            locomotive_number=number,
            passport_id=passport.id if passport else None,
        )

    @staticmethod
    def _validate_manufacture_dates(case_data: CaseCreate | CaseUpdate) -> None:
        """Проверяет отсутствие букв в датах изготовления"""
        data = case_data.model_dump(exclude_unset=True)
        for field in (
            "component_manufacture_date_old",
            "element_manufacture_date_old",
            "component_manufacture_date_new",
            "element_manufacture_date_new",
        ):
            value = data.get(field)
            if value is not None and any(character.isalpha() for character in value):
                raise CaseValidationError(field)

    @staticmethod
    def _normalize_installed_serials(
        data: dict, case: RepairCaseEquipment | None = None
    ) -> None:
        """Подставляет б/н вместо пустого номера выбранного установленного оборудования"""
        for role in ("component", "element"):
            field = role + "_serial_number_new"
            id_field = "new_" + role + "_equipment_id"
            equipment_id = data.get(id_field, getattr(case, id_field, None))
            if equipment_id and (field in data or id_field in data):
                value = data.get(field, getattr(case, field, None))
                data[field] = (value or "").strip() or "б/н"

    @staticmethod
    async def _get_case_with_relations(
        session: AsyncSession, case_id: int
    ) -> RepairCaseEquipment | None:
        """Внутренний метод для загрузки случая со всеми связями"""
        case = await CaseStatusService.get_case_with_status(
            session, case_id, load_detail_relations
        )
        return await PassportCaseService.case_details(session, case) if case else None

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
        actor_id: int | None = None,
    ) -> RepairCaseEquipment:
        """Создание случая"""

        CaseService._validate_manufacture_dates(case_data)
        case_creation_data = case_data.model_dump(
            exclude={
                "warranty_work",
                "user_id",
                "waybill_doc",
                "passport_links",
                "replacement_items",
                "expected_revision",
            }
        )
        CaseService._normalize_installed_serials(case_creation_data)
        await CaseService._prepare_locomotive(session, case_creation_data)

        # Разделение данных
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
        actor = await session.get(User, actor_id or user_id)
        case.created_by_id = actor.id
        case.created_by_name = actor.full_name or actor.login
        case.creator_source = "created"

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
        new_eq_id = case.new_element_equipment_id or case.new_component_equipment_id
        case.new_supplier_id = await EquipmentService.resolve_supplier(
            session,
            equipment_id=new_eq_id,
            locomotive_number=case.locomotive_number,
            locomotive_model_id=case.locomotive_model_id,
        )

        session.add(case)
        await session.flush()

        await PassportCaseService.sync_case(
            session,
            case,
            actor,
            links=[x.model_dump() for x in (case_data.passport_links or [])],
            installed=[x.model_dump() for x in (case_data.replacement_items or [])],
        )
        # Проверка на точный дубликат перед созданием
        await CaseService._check_duplicate(session, case)

        # Получаем объект со всеми связями и вычисленным статусом
        created_case = await CaseService._get_case_with_relations(session, case.id)
        return created_case

    @staticmethod
    @transactional
    async def update_case(
        session: AsyncSession,
        case_id: int,
        case_data: CaseUpdate,
        current_user_id: int | None = None,
    ) -> RepairCaseEquipment | None:
        """Обновление случая и автоматическое определение обоих поставщиков"""
        CaseService._validate_manufacture_dates(case_data)
        case = await session.scalar(
            select(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if not case:
            return None

        old_duplicate_identity = CaseService._duplicate_identity(case)
        if is_case_lock_active(case) and case.locked_by_id != current_user_id:
            raise CaseValidationError(
                "revision", "Случай сейчас редактирует другой пользователь"
            )
        update_data = case_data.model_dump(
            exclude_unset=True,
            exclude={
                "warranty_work",
                "waybill_doc",
                "passport_links",
                "replacement_items",
                "expected_revision",
            },
        )
        if (
            case_data.expected_revision is not None
            and case_data.expected_revision != case.revision
        ):
            raise CaseValidationError(
                "revision", "Случай изменён другим пользователем. Обновите карточку."
            )
        old_passport_id = case.passport_id
        await CaseService._prepare_locomotive(session, update_data, case)
        if update_data.get("passport_id", old_passport_id) != old_passport_id:
            existing_links = (
                await session.scalars(
                    select(CasePassportLink).where(CasePassportLink.case_id == case_id)
                )
            ).first()
            if existing_links:
                raise CaseValidationError(
                    "passport_id",
                    "У случая есть паспортные связи. Смена локомотива требует отдельного переноса связей.",
                )

        # Автоматическая смена владельца после проверки входных данных
        if current_user_id and case.user_id != current_user_id:
            case.user_id = current_user_id

        eq_changed = "component_equipment_id" in update_data
        el_changed = "element_equipment_id" in update_data
        new_eq_changed = "new_component_equipment_id" in update_data
        new_el_changed = "new_element_equipment_id" in update_data
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
                # Вызываем метод с проверкой исключений
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

        if new_eq_changed or new_el_changed or loco_num_changed or loco_model_changed:
            new_el_id = update_data.get(
                "new_element_equipment_id", case.new_element_equipment_id
            )
            new_comp_id = update_data.get(
                "new_component_equipment_id", case.new_component_equipment_id
            )
            update_data["new_supplier_id"] = await EquipmentService.resolve_supplier(
                session,
                equipment_id=new_el_id or new_comp_id,
                locomotive_number=update_data.get(
                    "locomotive_number", case.locomotive_number
                ),
                locomotive_model_id=update_data.get(
                    "locomotive_model_id", case.locomotive_model_id
                ),
            )

        # Обновляем поля
        CaseService._normalize_installed_serials(update_data, case)
        for field, value in update_data.items():
            setattr(case, field, value)

        await session.flush()

        relevant = {
            "fault_date",
            "section_mask",
            "component_equipment_id",
            "element_equipment_id",
            "repair_type_id",
            "malfunction_id",
            "component_serial_number_new",
            "element_serial_number_new",
            "component_manufacture_date_new",
            "element_manufacture_date_new",
        }
        actor = await session.get(User, current_user_id or case.user_id)
        linked_roles = set(
            (
                await session.scalars(
                    select(CasePassportLink.role).where(
                        CasePassportLink.case_id == case.id
                    )
                )
            ).all()
        )
        has_links = bool(linked_roles)
        if has_links and case_data.expected_revision is None:
            raise CaseValidationError(
                "revision", "Для сохранения связанных позиций обновите карточку случая"
            )
        protected = {
            f"{role}_{kind}_old"
            for role in linked_roles
            for kind in ("serial_number", "manufacture_date")
        }
        protected |= {f"{role}_quantity" for role in linked_roles}
        if (
            has_links
            and case_data.passport_links is None
            and protected.intersection(update_data)
        ):
            raise CaseValidationError(
                "passport_links",
                "Номера, даты и количество снятого оборудования определяются выбором паспортных позиций",
            )
        await PassportCaseService.sync_case(
            session,
            case,
            actor,
            links=(
                [x.model_dump() for x in case_data.passport_links]
                if case_data.passport_links is not None
                else None
            ),
            installed=(
                [x.model_dump() for x in case_data.replacement_items]
                if case_data.replacement_items is not None
                else None
            ),
            expected_revision=case_data.expected_revision,
            force=bool(
                has_links
                and (
                    relevant.intersection(update_data)
                    or case_data.replacement_items is not None
                )
            ),
        )
        if old_duplicate_identity != CaseService._duplicate_identity(case):
            await CaseService._check_duplicate(session, case)
        case.revision += 1

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

        # Сброс блокировки при успешном сохранении
        case.locked_by_id = None
        case.locked_at = None

        return await CaseService._get_case_with_relations(session, case.id)

    @staticmethod
    @transactional
    async def lock_case(
        session: AsyncSession, case_id: int, user_id: int
    ) -> RepairCaseEquipment:
        """Попытка заблокировать случай для редактирования"""
        stmt = (
            select(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
            .options(selectinload(RepairCaseEquipment.locked_by))
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            raise ValueError("Случай не найден")

        now = datetime.now(timezone.utc)

        # Проверка текущей блокировки
        if case.locked_by_id and case.locked_by_id != user_id:
            if is_case_lock_active(case, now):
                locker_name = (
                    case.locked_by.full_name
                    if case.locked_by
                    else "Другой пользователь"
                )
                raise ValueError(locker_name)

        # Установка или обновление блокировки
        case.locked_by_id = user_id
        case.locked_at = now
        await session.flush()

        return await CaseService._get_case_with_relations(session, case.id)

    @staticmethod
    @transactional
    async def heartbeat_case(session: AsyncSession, case_id: int, user_id: int):
        """Продлевает свою блокировку, но никогда не захватывает чужую или снятую"""
        case = await session.scalar(
            select(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if case is None or case.locked_by_id != user_id:
            raise ValueError("Блокировка редактирования больше не принадлежит вам")
        case.locked_at = datetime.now(timezone.utc)
        await session.flush()
        return {"lock_expires_at": case.lock_expires_at}

    @staticmethod
    @transactional
    async def unlock_case(session: AsyncSession, case_id: int, user_id: int) -> bool:
        """Снятие блокировки со случая"""
        case = await session.scalar(
            select(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if not case:
            return False

        # Повторное снятие безопасно; чужую блокировку не трогаем.
        if case.locked_by_id is None or case.locked_by_id == user_id:
            case.locked_by_id = None
            case.locked_at = None
            await session.flush()
            return True

        return False

    @staticmethod
    @transactional
    async def delete_case(
        session: AsyncSession, case_id: int, actor_id: int | None = None
    ) -> int:
        """Удаление случая со всеми его данными"""
        stmt = (
            select(RepairCaseEquipment)
            .where(RepairCaseEquipment.id == case_id)
            .with_for_update()
            .execution_options(populate_existing=True)
            .options(selectinload(RepairCaseEquipment.files))
        )
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            return 1

        actor = await session.get(User, actor_id or case.user_id)
        await PassportCaseService.delete_case(session, case, actor)

        if case.files:
            for file_rec in case.files:
                await FileManagementService.delete_file(session, file_rec.id)

        await session.delete(case)

        return 1

    @staticmethod
    async def _check_duplicate(session, case):
        """Проверяет точный дубликат с учётом выбранных экземпляров"""
        key = f"{case.fault_date}:{case.passport_id or case.locomotive_number}:{case.mileage}:{case.malfunction_id}:{case.passport_selection_key or case.component_equipment_id}"
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": key},
        )
        stmt = select(RepairCaseEquipment.id).where(
            RepairCaseEquipment.id != case.id,
            RepairCaseEquipment.fault_date == case.fault_date,
            RepairCaseEquipment.malfunction_id == case.malfunction_id,
            RepairCaseEquipment.mileage.is_not_distinct_from(case.mileage),
        )
        if case.passport_selection_key:
            stmt = stmt.where(
                RepairCaseEquipment.passport_id == case.passport_id,
                RepairCaseEquipment.passport_selection_key
                == case.passport_selection_key,
            )
        else:
            stmt = stmt.where(
                RepairCaseEquipment.locomotive_number == case.locomotive_number,
                RepairCaseEquipment.component_equipment_id
                == case.component_equipment_id,
                RepairCaseEquipment.element_equipment_id.is_not_distinct_from(
                    case.element_equipment_id
                ),
                RepairCaseEquipment.passport_selection_key.is_(None),
            )
        if await session.scalar(stmt.limit(1)):
            raise CaseValidationError("duplicate", "Такой случай уже существует")

    @staticmethod
    def _duplicate_identity(case):
        """Собирает поля случая, участвующие в проверке дубликата"""
        return (
            case.fault_date,
            case.passport_id,
            case.locomotive_number,
            case.mileage,
            case.component_equipment_id,
            case.element_equipment_id,
            case.malfunction_id,
            case.passport_selection_key,
        )
