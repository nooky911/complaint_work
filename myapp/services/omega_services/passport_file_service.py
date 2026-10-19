import asyncio
import logging
import re
from pathlib import Path
from sqlalchemy import select, func

from myapp.database.transactional import transactional
from myapp.services import CaseValidationError
from myapp.models.product_passports import (
    ProductPassport,
    ProductPassportNode,
    ProductPassportEvent,
    ProductPassportEventItem,
    ProductPassportFile,
)
from myapp.omega.stock_client import OmegaStockClient
from myapp.schemas.files import FileCategory
from myapp.services.storage_service import StorageService
from myapp.validators.file_validator import FileValidator, MAX_FILE_SIZE, MAX_CASE_SIZE

logger = logging.getLogger(__name__)


class PassportFileService:
    """Файлы заводского оборудования Omega и загруженные сканы экземпляров"""

    @staticmethod
    async def timeline(session, passport_id, node_id):
        """Читает позицию и редакции её истории в порядке замен"""
        node = await session.get(ProductPassportNode, node_id)
        if node is None or node.passport_id != passport_id:
            raise FileNotFoundError("Позиция паспорта не найдена")
        rows = (
            await session.execute(
                select(ProductPassportEvent, ProductPassportEventItem)
                .join(ProductPassportEventItem)
                .where(
                    ProductPassportEventItem.node_id == node_id,
                    ProductPassportEvent.passport_id == passport_id,
                )
                .order_by(
                    ProductPassportEvent.effective_date,
                    ProductPassportEvent.day_order,
                    ProductPassportEvent.id,
                )
            )
        ).all()
        return node, rows

    @staticmethod
    def next_instance(event, current):
        """Меняет ключ экземпляра только при замене, сохраняя его при исправлении"""
        if event.kind not in ("case_replacement", "historical_replacement"):
            return current
        return (
            f"case:{event.source_case_id}"
            if event.source_case_id is not None
            else f"event:{event.id}"
        )

    @staticmethod
    def instance_signature(state):
        """Сравнивает оборудование и заводской номер при разрыве цепочки замен"""
        state = state or {}
        return (
            state.get("equipment_id"),
            str(state.get("serial_number") or "").strip().casefold(),
        )

    @classmethod
    def instance_targets(cls, node, rows):
        """Сохраняет принадлежность сканов при отмене прежних замен"""
        key = "factory"
        previous = node.baseline_state
        targets = {}
        for event, item in rows:
            if event.status != "active":
                continue
            before = key
            if (
                event.kind in ("case_replacement", "historical_replacement")
                and previous is not None
                and cls.instance_signature(previous)
                != cls.instance_signature(item.before_state)
            ):
                # Отменённая замена не должна делать снятый позднее экземпляр заводским
                signature = cls.instance_signature(item.before_state)
                candidates = set()
                if signature[1] not in ("", "б/н", "-", "—"):
                    for earlier, change in rows:
                        if earlier.id == event.id:
                            break
                        if (
                            earlier.kind
                            in ("case_replacement", "historical_replacement")
                            and cls.instance_signature(change.after_state) == signature
                        ):
                            candidates.add(cls.next_instance(earlier, "factory"))
                before = (
                    next(iter(candidates))
                    if len(candidates) == 1
                    else (
                        f"removed-case:{event.source_case_id}"
                        if event.source_case_id is not None
                        else f"removed-event:{event.id}"
                    )
                )
            key = cls.next_instance(event, key)
            targets[event.id] = (before, key)
            previous = item.after_state
        return targets, key

    @classmethod
    async def target(cls, session, passport_id, node_id, event_id=None, side="before"):
        """Определяет экземпляр по истории без изменения снимков"""
        node, rows = await cls.timeline(session, passport_id, node_id)
        targets, current = cls.instance_targets(node, rows)
        if event_id is None:
            return node, current
        if event_id not in targets:
            raise CaseValidationError(
                "revision", "Запись истории изменилась. Обновите историю"
            )
        return node, targets[event_id][0 if side == "before" else 1]

    @staticmethod
    def omega_files(object_code):
        """Читает имена прямых вложений паспортного узла без скачивания"""
        client = OmegaStockClient()
        with client._get_connection() as connection:
            connection.call_timeout = 30000
            return client._fetch_all(
                connection,
                """
                SELECT DISTINCT a.DOCUMENT AS ID,
                    COALESCE(p.FILENAME,p.NAME,'Вложение ' || TO_CHAR(a.DOCUMENT)) AS NAME
                FROM OMP_ADM.ATTACHMENTS a
                LEFT JOIN OMP_ADM.DOCUMENTS_PARAMS p ON p.CODE=a.DOCUMENT
                WHERE a.BUSINESSOBJ=:object_code
                ORDER BY NAME,ID
            """,
                object_code=object_code,
            )

    @staticmethod
    def local_description(file):
        """Возвращает свойства пользовательского файла без пути на диске"""
        return dict(
            id=file.id,
            name=file.original_name,
            source="local",
            size_bytes=file.size_bytes,
            uploaded_by=file.uploaded_by_name,
            uploaded_at=file.uploaded_at,
        )

    @classmethod
    async def file_lists(cls, session, node, keys):
        """Читает файлы всех нужных экземпляров одним запросом к каждой БД"""
        local = (
            await session.scalars(
                select(ProductPassportFile)
                .where(
                    ProductPassportFile.node_id == node.id,
                    ProductPassportFile.instance_key.in_(keys),
                )
                .order_by(ProductPassportFile.uploaded_at, ProductPassportFile.id)
            )
        ).all()
        result = {
            key: dict(instance_key=key, files=[], omega_error=None) for key in keys
        }
        for file in local:
            result[file.instance_key]["files"].append(cls.local_description(file))
        if "factory" in result:
            try:
                remote = await asyncio.to_thread(cls.omega_files, node.omega_code)
                result["factory"]["files"] = [
                    dict(id=r["id"], name=r["name"], source="omega") for r in remote
                ] + result["factory"]["files"]
            except Exception:
                logger.exception("Не удалось получить вложения Omega узла %s", node.id)
                result["factory"][
                    "omega_error"
                ] = "Не удалось получить заводские файлы из Omega"
        return result

    @classmethod
    async def listing(cls, session, passport_id, node_id, event_id=None, side="before"):
        """Возвращает сканы выбранного экземпляра и ссылки на заводские вложения"""
        node, key = await cls.target(session, passport_id, node_id, event_id, side)
        return (await cls.file_lists(session, node, {key}))[key]

    @classmethod
    async def history_files(cls, session, passport_id, node_id):
        """Получает файлы всей истории без отдельных запросов для каждой строки"""
        node, rows = await cls.timeline(session, passport_id, node_id)
        targets, _ = cls.instance_targets(node, rows)
        keys = {key for pair in targets.values() for key in pair}
        files = await cls.file_lists(session, node, keys)
        return {
            event_id: dict(before=files[before], after=files[after])
            for event_id, (before, after) in targets.items()
        }

    @classmethod
    async def omega_content(
        cls,
        session,
        passport_id,
        node_id,
        file_id,
        expected_key,
        event_id=None,
        side="before",
    ):
        """Проверяет экземпляр и читает вложение существующим механизмом ТТН"""
        node, key = await cls.target(session, passport_id, node_id, event_id, side)
        if key != "factory" or key != expected_key:
            raise CaseValidationError(
                "revision", "Оборудование изменилось. Обновите список файлов"
            )
        try:
            files = await asyncio.to_thread(cls.omega_files, node.omega_code)
            metadata = next((f for f in files if f["id"] == file_id), None)
            if metadata is None:
                raise FileNotFoundError("Вложение не найдено")
            content = await asyncio.to_thread(
                OmegaStockClient().get_file, node.omega_code, file_id
            )
        except FileNotFoundError:
            raise
        except Exception:
            logger.exception("Не удалось прочитать файл Omega %s", file_id)
            raise ConnectionError(
                "Не удалось скачать файл из Omega. Повторите позже"
            ) from None
        if content is None:
            raise FileNotFoundError("Вложение не найдено")
        return content, metadata["name"]

    @staticmethod
    async def local_file(session, passport_id, node_id, file_id):
        """Проверяет принадлежность локального файла позиции паспорта"""
        file = await session.scalar(
            select(ProductPassportFile)
            .join(ProductPassportNode)
            .where(
                ProductPassportFile.id == file_id,
                ProductPassportFile.node_id == node_id,
                ProductPassportNode.passport_id == passport_id,
            )
        )
        if file is None:
            raise FileNotFoundError("Файл не найден")
        path = StorageService.get_full_path(file.file_path)
        if not path.is_file():
            raise FileNotFoundError("Файл отсутствует в хранилище")
        return file, path

    @classmethod
    async def upload(
        cls,
        session,
        passport_id,
        node_id,
        files,
        actor,
        expected_key,
        event_id=None,
        side="before",
    ):
        """Загружает сканы и убирает записанные файлы при откате транзакции"""
        created_paths = []
        try:
            return await cls._upload(
                session,
                passport_id,
                node_id,
                files,
                actor,
                expected_key,
                event_id,
                side,
                created_paths,
            )
        except BaseException:
            for path in created_paths:
                await asyncio.to_thread(path.unlink, missing_ok=True)
            raise
        finally:
            for file in files:
                await file.close()

    @classmethod
    @transactional
    async def _upload(
        cls,
        session,
        passport_id,
        node_id,
        files,
        actor,
        expected_key,
        event_id,
        side,
        created_paths,
    ):
        """Сохраняет файлы только если экземпляр не изменился за время загрузки"""
        passport = await session.scalar(
            select(ProductPassport)
            .where(ProductPassport.id == passport_id)
            .with_for_update()
        )
        if passport is None:
            raise FileNotFoundError("Паспорт не найден")
        _, key = await cls.target(session, passport_id, node_id, event_id, side)
        if key != expected_key:
            raise CaseValidationError(
                "revision", "Оборудование изменилось. Обновите список файлов"
            )
        if not files or len(files) > 20:
            raise ValueError("Выберите от одного до двадцати файлов")
        total = await session.scalar(
            select(func.coalesce(func.sum(ProductPassportFile.size_bytes), 0)).where(
                ProductPassportFile.node_id == node_id,
                ProductPassportFile.instance_key == key,
            )
        )
        prepared = []
        for file in files:
            content = await file.read(MAX_FILE_SIZE + 1)
            file.size = len(content)
            await file.seek(0)
            FileValidator.validate_file(file, FileCategory.waybill)
            name = Path((file.filename or "Скан паспорта").replace("\\", "/")).name
            name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()
            if not name or len(name) > 255:
                raise ValueError("Некорректное имя файла")
            total += file.size
            prepared.append((file, name))
        if total > MAX_CASE_SIZE:
            raise ValueError("Общий размер сканов экземпляра превышает 50 МБ")
        number = re.sub(r"[^\w-]", "_", passport.product_number)[:60]
        folder = f"passports/{number}_{passport.id}/{node_id}"
        uploaded = []
        for file, name in prepared:
            relative = f"{folder}/{StorageService.generate_stored_name(name)}"
            path = StorageService.get_full_path(relative)
            created_paths.append(path)
            await StorageService.save_file_to_disk(file, relative)
            record = ProductPassportFile(
                node_id=node_id,
                instance_key=key,
                original_name=name,
                file_path=relative,
                mime_type=file.content_type,
                size_bytes=file.size,
                uploaded_by_id=actor.id,
                uploaded_by_name=actor.full_name or actor.login,
            )
            session.add(record)
            await session.flush()
            uploaded.append(cls.local_description(record))
        return uploaded
