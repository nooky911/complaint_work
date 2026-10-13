from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta

from myapp.models import WaybillDoc
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.warranty_work import WarrantyWork
from myapp.schemas.cases import CaseCreate, CaseUpdate
from myapp.database.query_builders.query_case_builders import load_detail_relations
from myapp.database.transactional import transactional
from myapp.services.equipment_service import EquipmentService
from myapp.services.warranty_service import WarrantyService
from myapp.services.case_status_service import CaseStatusService
from myapp.services.waybill_service import WaybillService
from myapp.services.files.file_management_service import FileManagementService
from myapp.models.auxiliaries import LocomotiveNumberException
from myapp.models.product_passports import ProductPassport
from myapp.services.product_passport_service import ProductPassportService


class CaseValidationError(ValueError):
    """Ошибка входных данных случая, отличная от ошибки дубликата"""

    def __init__(self, field: str, message: str = "Дата изготовления не должна содержать буквы"):
        self.field = field
        super().__init__(message)


class CaseService:

    @staticmethod
    async def _prepare_locomotive(session: AsyncSession, data: dict, case=None) -> None:
        identity_fields = ("locomotive_model_id", "locomotive_number", "section_mask", "passport_id")
        if case is not None and case.locomotive_identity_locked:
            for field in identity_fields:
                if field in data and data[field] != getattr(case, field):
                    raise CaseValidationError(field, "Модель, номер и секции этого архивного случая изменять нельзя")
            return
        if case is not None and not any(field in data for field in identity_fields):
            return

        passport = None
        if data.get("passport_id") is not None:
            passport = await session.get(ProductPassport, data["passport_id"])
            if passport is None:
                raise CaseValidationError("passport_id", "Выбранный паспорт не найден")
            for field, value in (("locomotive_model_id", passport.locomotive_model_id),
                                 ("locomotive_number", passport.product_number)):
                if field in data and data[field] is not None and data[field] != value:
                    raise CaseValidationError(field, "Модель или номер не соответствует выбранному паспорту")
            model_id, number = passport.locomotive_model_id, passport.product_number
        else:
            model_id = data.get("locomotive_model_id", getattr(case, "locomotive_model_id", None))
            number = data.get("locomotive_number", getattr(case, "locomotive_number", None))
            if model_id is None or not isinstance(number, str) or not number.strip():
                raise CaseValidationError("locomotive_number", "Выберите модель и номер локомотива")
            number = number.strip()

        exception = await session.get(LocomotiveNumberException, (model_id, number))
        if exception is not None:
            if passport is not None:
                raise CaseValidationError("passport_id", "Этот локомотив используется без привязки к паспорту")
            allowed_mask = exception.section_mask
        else:
            if passport is None:
                passport = await session.scalar(select(ProductPassport).where(
                    ProductPassport.locomotive_model_id == model_id,
                    ProductPassport.product_number == number,
                ))
            if passport is None:
                raise CaseValidationError("locomotive_number", "Номер недоступен для этой модели: нужен паспорт или разрешённое исключение")
            masks = await ProductPassportService.get_section_masks(session, [passport.id])
            allowed_mask = masks.get(passport.id, 0)
            if not allowed_mask:
                raise CaseValidationError("section_mask", "В паспорте не удалось определить доступные секции")

        mask = data.get("section_mask", getattr(case, "section_mask", None))
        if type(mask) is not int or mask <= 0 or mask & ~allowed_mask:
            raise CaseValidationError("section_mask", "Выбранные секции отсутствуют у этого локомотива")
        data.update(locomotive_model_id=model_id, locomotive_number=number,
                    passport_id=passport.id if passport else None)

    @staticmethod
    def _validate_manufacture_dates(case_data: CaseCreate | CaseUpdate) -> None:
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

        CaseService._validate_manufacture_dates(case_data)
        case_creation_data = case_data.model_dump(exclude={"warranty_work", "user_id", "waybill_doc"})
        await CaseService._prepare_locomotive(session, case_creation_data)

        # Проверка на точный дубликат перед созданием
        existing_case = await session.execute(
            select(RepairCaseEquipment).where(
                RepairCaseEquipment.fault_date == case_data.fault_date,
                RepairCaseEquipment.locomotive_number == case_creation_data["locomotive_number"],
                RepairCaseEquipment.component_equipment_id
                == case_data.component_equipment_id,
                or_(
                    RepairCaseEquipment.element_equipment_id
                    == case_data.element_equipment_id,
                    RepairCaseEquipment.element_equipment_id.is_(None)
                    & (case_data.element_equipment_id is None),
                ),
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
        new_eq_id = case.new_element_equipment_id or case.new_component_equipment_id
        case.new_supplier_id = await EquipmentService.resolve_supplier(
            session,
            equipment_id=new_eq_id,
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
        session: AsyncSession,
        case_id: int,
        case_data: CaseUpdate,
        current_user_id: int | None = None,
    ) -> RepairCaseEquipment | None:
        """Обновление случая и автоматическое определение обоих поставщиков"""
        CaseService._validate_manufacture_dates(case_data)
        case: RepairCaseEquipment | None = await session.get(
            RepairCaseEquipment, case_id
        )
        if not case:
            return None

        update_data = case_data.model_dump(
            exclude_unset=True, exclude={"warranty_work", "waybill_doc"}
        )
        await CaseService._prepare_locomotive(session, update_data, case)

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
        )
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            raise ValueError("Случай не найден")

        now = datetime.now(timezone.utc)
        timeout = timedelta(minutes=30)

        # Проверка текущей блокировки
        if case.locked_by_id and case.locked_by_id != user_id:
            if case.locked_at and (now - case.locked_at) < timeout:
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
    async def unlock_case(session: AsyncSession, case_id: int, user_id: int) -> bool:
        """Снятие блокировки со случая"""
        case = await session.get(RepairCaseEquipment, case_id)
        if not case:
            return False

        # Снимаем только если блокировка принадлежит текущему пользователю или если мы суперадмин
        if case.locked_by_id == user_id:
            case.locked_by_id = None
            case.locked_at = None
            await session.flush()
            return True

        return False

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
                await FileManagementService.delete_file(session, file_rec.id)

        await session.delete(case)

        return 1
