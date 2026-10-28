import asyncio
from datetime import date, datetime, timezone
from myapp.constants.case_lock import is_case_lock_active
from myapp.services.user_access_service import UserAccessService
import hashlib
import hmac
from io import BytesIO
import json
import logging
from fastapi import UploadFile
from sqlalchemy import (
    SQLColumnExpression,
    String,
    and_,
    case,
    func,
    literal,
    or_,
    select,
    true,
)
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Subquery
from starlette.datastructures import Headers

from myapp.config import settings
from myapp.database.transactional import transactional
from myapp.models.auxiliaries import (
    LocomotiveModel,
    RegionalCenter,
    RepairType,
    Supplier,
)
from myapp.models.case_files import CaseFile, FileCategory, WaybillDocumentField
from myapp.models.equipment_malfunctions import Equipment
from myapp.models.repair_case_equipment import RepairCaseEquipment
from myapp.models.user import User
from myapp.models.warranty_work import WarrantyWork
from myapp.models.waybill_docs import ShippingProvider
from myapp.services import CaseValidationError
from myapp.services.case_filter_service import CaseFilterService
from myapp.services.omega_services.omega_stock_service import OmegaStockService
from myapp.services.storage_service import StorageService
from myapp.services.waybill_service import WaybillService
from myapp.schemas.waybill import WaybillDocUpdate
from myapp.schemas.omega_stock import OmegaStockCaseLinkRequest, OmegaStockColumnFilter
from myapp.validators.file_validator import FileValidator, MAX_CASE_SIZE

logger = logging.getLogger(__name__)


class StockCaseLinkService:
    """Копирует складской документ в существующие поля и вложения случая"""

    FIELDS = {
        "receipts": {"ttn_replacement", "ttn_from_supplier"},
        "inplant": {"ttn_from_rc"},
        "outbound": {"ttn_to_supplier"},
    }
    PROVIDERS = {
        "ttn_to_supplier": "to_supplier_provider_id",
        "ttn_from_supplier": "from_supplier_provider_id",
    }
    COLUMNS = (
        "display_number",
        "regional_center",
        "locomotive",
        "equipment",
        "serial",
        "supplier",
        "notification",
        "act",
    )

    @staticmethod
    def access_condition(user: User) -> ColumnElement[bool]:
        """Ограничивает выбор владельцем случая и разрешённым напарником"""
        if user.role == "superadmin":
            return true()
        owner = RepairCaseEquipment.user_id == user.id
        if user.role != "editor":
            return literal(False)
        return or_(owner, RepairCaseEquipment.user_id.in_(UserAccessService.partner_ids(user.id)))

    @staticmethod
    def _document_text(
        number: SQLColumnExpression[str | None],
        doc_date: SQLColumnExpression[date | None],
    ) -> ColumnElement[str | None]:
        """Формирует номер и дату документа для таблицы выбора"""
        return case(
            (
                number.is_not(None),
                func.concat(
                    number,
                    case(
                        (
                            doc_date.is_not(None),
                            func.concat(" от ", func.to_char(doc_date, "DD.MM.YYYY")),
                        ),
                        else_="",
                    ),
                ),
            ),
            else_=None,
        )

    @classmethod
    def _case_table(cls, user: User) -> Subquery:
        """Собирает колонки выбора с общими номерами случаев до фильтрации"""
        r = RepairCaseEquipment
        numbered = CaseFilterService._numbered_cases()
        show_element = and_(
            r.element_equipment_id.is_not(None),
            r.repair_type_id.in_(
                select(RepairType.id).where(RepairType.auto_fill_strategy == "LEVEL_4")
            ),
        )
        # Ближайший поставщик в классификаторе определяет обозначение оборудования
        ancestors = (
            select(
                r.id.label("case_id"),
                Equipment.id.label("equipment_id"),
                Equipment.parent_id,
                Equipment.supplier_id,
                Equipment.equipment_name,
                literal(0).label("depth"),
                show_element.label("show_element"),
            )
            .join(
                Equipment,
                Equipment.id
                == case(
                    (show_element, r.element_equipment_id),
                    else_=r.component_equipment_id,
                ),
            )
            .where(cls.access_condition(user))
            .cte("stock_equipment", recursive=True)
        )
        ancestors = ancestors.union_all(
            select(
                ancestors.c.case_id,
                Equipment.id,
                Equipment.parent_id,
                Equipment.supplier_id,
                Equipment.equipment_name,
                ancestors.c.depth + 1,
                ancestors.c.show_element,
            )
            .join(Equipment, Equipment.id == ancestors.c.parent_id)
            .where(
                ~ancestors.c.show_element,
                ancestors.c.supplier_id.is_(None),
                ancestors.c.depth < 30,
            )
        )
        equipment = (
            select(
                ancestors.c.case_id,
                ancestors.c.equipment_name,
            )
            .distinct(ancestors.c.case_id)
            .order_by(
                ancestors.c.case_id,
                case((ancestors.c.supplier_id.is_not(None), 0), else_=1),
                ancestors.c.depth,
            )
            .subquery()
        )
        serial = case(
            (show_element, r.element_serial_number_old),
            else_=r.component_serial_number_old,
        )
        made = case(
            (show_element, r.element_manufacture_date_old),
            else_=r.component_manufacture_date_old,
        )
        serial_text = case(
            (
                serial.is_not(None),
                func.concat(
                    serial,
                    case(
                        (
                            and_(made.is_not(None), made != ""),
                            func.concat(" (", made, ")"),
                        ),
                        else_="",
                    ),
                ),
            ),
            else_=None,
        )
        w = WarrantyWork
        repeated = and_(
            w.re_notification_number.is_not(None), w.re_notification_number != ""
        )
        claim = and_(w.claim_act_number.is_not(None), w.claim_act_number != "")
        return (
            select(
                r.id,
                numbered.c.display_number.cast(String).label("display_number"),
                RegionalCenter.regional_center_name.label("regional_center"),
                func.concat(
                    LocomotiveModel.locomotive_model_name, " ", r.locomotive_number
                ).label("locomotive"),
                equipment.c.equipment_name.label("equipment"),
                serial_text.label("serial"),
                Supplier.supplier_name.label("supplier"),
                cls._document_text(
                    case(
                        (repeated, w.re_notification_number),
                        else_=w.notification_number,
                    ),
                    case((repeated, w.re_notification_date), else_=w.notification_date),
                ).label("notification"),
                cls._document_text(
                    case(
                        (claim, w.claim_act_number), else_=w.work_completion_act_number
                    ),
                    case((claim, w.claim_act_date), else_=w.work_completion_act_date),
                ).label("act"),
            )
            .join(numbered, r.id == numbered.c.id)
            .join(LocomotiveModel)
            .join(RegionalCenter, r.regional_center_id == RegionalCenter.id)
            .outerjoin(equipment, r.id == equipment.c.case_id)
            .outerjoin(Supplier, Supplier.id == r.supplier_id)
            .outerjoin(w, w.case_id == r.id)
            .where(cls.access_condition(user))
            .subquery("stock_cases")
        )

    @classmethod
    def _conditions(
        cls,
        table: Subquery,
        filters: dict[str, OmegaStockColumnFilter],
        except_column: str | None = None,
    ) -> list[ColumnElement[bool]]:
        """Проверяет и применяет мультифильтры колонок"""
        conditions = []
        for column, selection in filters.items():
            if column not in cls.COLUMNS:
                raise ValueError("Неизвестная колонка фильтра")
            if len(selection.values) > 10000 or any(
                v is not None and len(v) > 2000 for v in selection.values
            ):
                raise ValueError("Слишком большой фильтр")
            if column == except_column:
                continue
            expr = table.c[column]
            values = [v for v in selection.values if v is not None]
            match = (
                or_(expr.in_(values), expr.is_(None))
                if None in selection.values
                else expr.in_(values)
            )
            if selection.mode == "include":
                conditions.append(match)
            else:
                conditions.append(
                    ~match if None in selection.values else or_(expr.is_(None), ~match)
                )
        return conditions

    @classmethod
    async def list_cases(cls, session, user, filters, offset, limit, selected_ids=None):
        """Возвращает страницу доступных случаев, размещая выбранные в начале"""
        selected_ids = selected_ids or []
        if len(selected_ids) > 10000 or any(value <= 0 for value in selected_ids):
            raise ValueError("Некорректный список выбранных случаев")
        table = cls._case_table(user)
        conditions = cls._conditions(table, filters)
        ordering = []
        if selected_ids:
            ordering.append(case((table.c.id.in_(selected_ids), 0), else_=1))
        ordering.append(table.c.id.desc())
        total = await session.scalar(
            select(func.count()).select_from(table).where(*conditions)
        )
        items = (
            (
                await session.execute(
                    select(table)
                    .where(*conditions)
                    .order_by(*ordering)
                    .offset(offset)
                    .limit(limit)
                )
            )
            .mappings()
            .all()
        )
        return {"items": [dict(row) for row in items], "total": total}

    @classmethod
    async def filter_options(cls, session, user, column, filters):
        """Возвращает значения колонки в пределах прав пользователя"""
        if column not in cls.COLUMNS:
            raise ValueError("Неизвестная колонка фильтра")
        table = cls._case_table(user)
        return list(
            (
                await session.scalars(
                    select(table.c[column])
                    .distinct()
                    .where(*cls._conditions(table, filters, column))
                    .order_by(table.c[column])
                )
            ).all()
        )

    @classmethod
    async def _validate(cls, session, kind, data):
        """Проверяет назначение и введённые данные до обращения к складу"""
        if data.related_field not in cls.FIELDS.get(kind, set()):
            raise ValueError(
                "Этот вид складского документа нельзя перенести в выбранный блок"
            )
        if any(case_id <= 0 for case_id in data.case_ids):
            raise ValueError("Некорректный номер случая")
        if not data.number.strip():
            raise ValueError("Укажите номер документа")
        try:
            parsed = date.fromisoformat(data.document_date)
            if len(data.document_date) != 10 or parsed.year < 2000:
                raise ValueError
        except ValueError:
            raise ValueError(
                "Укажите полную дату документа в формате ДД.ММ.ГГГГ"
            ) from None
        provider_field = cls.PROVIDERS.get(data.related_field)
        if provider_field:
            if not data.provider_id or not await session.get(
                ShippingProvider, data.provider_id
            ):
                raise ValueError("Выберите перевозчика / действие")
            if data.related_field == "ttn_from_supplier" and data.provider_id > 5:
                raise ValueError("Это действие недоступно для возврата от поставщика")
        elif data.provider_id is not None:
            raise ValueError("В выбранном блоке нет перевозчика / действия")
        return {
            data.related_field: data.number.strip(),
            f"{data.related_field}_date": parsed,
            **({provider_field: data.provider_id} if provider_field else {}),
        }

    @classmethod
    async def _cases(cls, session, user, ids, lock=False):
        """Повторно проверяет доступ и блокировки перед изменением случаев"""
        statement = (
            select(RepairCaseEquipment)
            .where(RepairCaseEquipment.id.in_(ids), cls.access_condition(user))
            .order_by(RepairCaseEquipment.id)
            .options(
                selectinload(RepairCaseEquipment.waybill_doc),
                selectinload(RepairCaseEquipment.files),
            )
            .execution_options(populate_existing=True)
        )
        if lock:
            statement = statement.with_for_update()
        cases = list((await session.scalars(statement)).all())
        if {c.id for c in cases} != set(ids):
            raise PermissionError(
                "Часть выбранных случаев удалена или недоступна для изменения"
            )
        now = datetime.now(timezone.utc)
        for c in cases:
            if is_case_lock_active(c, now):
                raise CaseValidationError(
                    "revision",
                    "Один из случаев сейчас редактируется. Завершите редактирование и повторите привязку",
                )
        return cases

    @classmethod
    async def _preview(
        cls, session, user, data, cases, files, values, kind, document_id
    ):
        """Сохраняет в подписи проверенные данные без отдельной таблицы привязок"""
        numbered = CaseFilterService._numbered_cases()
        numbers = dict(
            (
                await session.execute(
                    select(numbered).where(numbered.c.id.in_([c.id for c in cases]))
                )
            ).all()
        )
        existing = []
        snapshot = []
        for c in cases:
            old = {key: getattr(c.waybill_doc, key, None) for key in values}
            attached = sorted(
                f.id
                for f in c.files
                if f.category == FileCategory.waybill
                and f.related_field == data.related_field
            )
            snapshot.append([c.id, c.user_id, c.revision, old, attached])
            if any(v is not None and v != "" for v in old.values()) or attached:
                provider_field = cls.PROVIDERS.get(data.related_field)
                provider = (
                    await session.get(ShippingProvider, old[provider_field])
                    if provider_field and old[provider_field]
                    else None
                )
                existing.append(
                    {
                        "id": c.id,
                        "display_number": numbers[c.id],
                        "number": old[data.related_field],
                        "document_date": old[f"{data.related_field}_date"],
                        "provider": provider.name if provider else None,
                        "file_count": len(attached),
                    }
                )
        content = json.dumps(
            [
                user.id,
                kind,
                document_id,
                values,
                snapshot,
                sorted(f["id"] for f in files),
            ],
            default=str,
            sort_keys=True,
        ).encode()
        token = hmac.new(
            settings.SECRET_KEY.encode(), content, hashlib.sha256
        ).hexdigest()
        return {
            "token": token,
            "existing": existing,
            "case_count": len(cases),
            "file_count": len(files),
        }

    @classmethod
    async def preview(cls, session, user, kind, document_id, data):
        """Показывает заполненные блоки до подтверждения замены"""
        values = await cls._validate(session, kind, data)
        cases = await cls._cases(session, user, data.case_ids)
        files = await OmegaStockService().list_files(kind, document_id)
        if files is None:
            raise FileNotFoundError("Складской документ не найден")
        return await cls._preview(
            session, user, data, cases, files, values, kind, document_id
        )

    @staticmethod
    def _upload(file_id, content):
        """Определяет формат вложения по содержимому, сохраняя номер Omega"""
        mime, suffix = "application/octet-stream", ""
        for signature, detected, extension in (
            (b"%PDF", "application/pdf", ".pdf"),
            (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
            (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
            (b"\xd0\xcf\x11\xe0", "application/vnd.ms-outlook", ".msg"),
        ):
            if content.startswith(signature):
                mime, suffix = detected, extension
                break
        return UploadFile(
            BytesIO(content),
            size=len(content),
            filename=f"omega-{file_id}{suffix}",
            headers=Headers({"content-type": mime}),
        )

    @staticmethod
    def _check_confirmation(data: OmegaStockCaseLinkRequest, preview: dict) -> None:
        """Проверяет актуальность подтверждения и разрешение на замену данных"""
        if not data.preview_token or not hmac.compare_digest(
            data.preview_token.encode(), preview["token"].encode()
        ):
            raise CaseValidationError(
                "revision", "Данные изменились. Проверьте перенос ещё раз"
            )
        if preview["existing"] and not data.confirm_overwrite:
            raise CaseValidationError(
                "revision", "Подтвердите замену заполненных данных"
            )

    @classmethod
    async def apply(cls, session, user, kind, document_id, data):
        """Скачивает вложения один раз и откатывает весь перенос при ошибке"""
        paths = []
        try:
            return await cls._apply(session, user, kind, document_id, data, paths)
        except BaseException:
            await session.rollback()
            for path in paths:
                try:
                    await asyncio.to_thread(path.unlink, missing_ok=True)
                except OSError:
                    logger.exception("Не удалось удалить файл после отмены привязки")
            raise

    @classmethod
    @transactional
    async def _apply(cls, session, user, kind, document_id, data, paths):
        """Сохраняет поля передвижения и все файлы одной общей транзакцией"""
        values = await cls._validate(session, kind, data)
        cases = await cls._cases(session, user, data.case_ids)
        stock = OmegaStockService()
        files = await stock.list_files(kind, document_id)
        if files is None:
            raise FileNotFoundError("Складской документ не найден")
        initial = await cls._preview(
            session, user, data, cases, files, values, kind, document_id
        )
        cls._check_confirmation(data, initial)
        contents = []
        for file in files:
            content = await stock.get_file(kind, document_id, file["id"])
            if content is None:
                raise FileNotFoundError(
                    "Один из файлов склада недоступен. Перенос отменён"
                )
            upload = cls._upload(file["id"], content)
            try:
                FileValidator.validate_file(upload, FileCategory.waybill)
            finally:
                await upload.close()
            contents.append((file["id"], content))
            if sum(len(body) for _, body in contents) > MAX_CASE_SIZE:
                raise ValueError(
                    "Вложения склада превышают лимит размера случая (50 МБ)"
                )
        cases = await cls._cases(session, user, data.case_ids, lock=True)
        preview = await cls._preview(
            session, user, data, cases, files, values, kind, document_id
        )
        cls._check_confirmation(data, preview)
        added = 0
        for c in cases:
            pending = []
            for file_id, content in contents:
                upload = cls._upload(file_id, content)
                matches = [
                    f
                    for f in c.files
                    if f.category == FileCategory.waybill
                    and f.related_field == data.related_field
                    and f.original_name == upload.filename
                    and f.size_bytes == len(content)
                ]
                duplicate = False
                for f in matches:
                    path = StorageService.get_full_path(f)
                    if (
                        path.is_file()
                        and await asyncio.to_thread(path.read_bytes) == content
                    ):
                        duplicate = True
                        break
                await upload.close()
                if not duplicate:
                    pending.append((file_id, content))
            if (
                sum(f.size_bytes for f in c.files)
                + sum(len(body) for _, body in pending)
                > MAX_CASE_SIZE
            ):
                raise ValueError(
                    f"Случай №{c.id}: вложения превышают общий лимит 50 МБ"
                )
            for file_id, content in pending:
                upload = cls._upload(file_id, content)
                stored = StorageService.generate_stored_name(upload.filename)
                relative = StorageService.get_relative_path(
                    c.id,
                    FileCategory.waybill,
                    stored,
                    WaybillDocumentField(data.related_field),
                )
                paths.append(StorageService.get_full_path(relative))
                await StorageService.save_file_to_disk(upload, relative)
                session.add(
                    CaseFile(
                        case_id=c.id,
                        category=FileCategory.waybill,
                        related_field=data.related_field,
                        original_name=upload.filename,
                        stored_name=stored,
                        file_path=relative,
                        mime_type=upload.content_type,
                        size_bytes=len(content),
                    )
                )
                added += 1
            await WaybillService.update_waybill_doc(
                session, c.id, WaybillDocUpdate(**values)
            )
            c.revision += 1
        await session.flush()
        return {"case_count": len(cases), "added_files": added}
