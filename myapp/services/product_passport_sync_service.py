import asyncio
import logging
import re
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from myapp.config import settings
from myapp.database.base import async_session_maker
from myapp.models.auxiliaries import LocomotiveModel, Supplier
from myapp.models.equipment_malfunctions import Equipment
from myapp.models.product_passports import (
    ProductPassport,
    ProductPassportNode,
    ProductPassportEquipmentMatch,
    ProductPassportEquipmentSerialMatch,
)
from myapp.omega.client import OmegaClient
from myapp.schemas.omega import OmegaPassportRootData
from myapp.ul_service.client import ULServiceClient
from myapp.services.product_passport_service import ProductPassportService
from myapp.services.product_passport_equipment_service import (
    NumberedPassportLinks,
    ProductPassportEquipmentService,
)
from myapp.validators.product_passport_validator import ProductPassportValidator

logger = logging.getLogger(__name__)
_sync_lock = asyncio.Lock()


class ProductPassportSyncService:
    """Однократная загрузка паспортов после ввода локомотива в эксплуатацию"""

    @staticmethod
    async def sync_new_passports() -> dict[str, int]:
        """Сначала проверяет UL-сервис, затем загружает подтверждённые паспорта"""
        if _sync_lock.locked():
            logger.info("Синхронизация паспортов уже выполняется")
            return {}

        async with _sync_lock:
            commissioning_dates = await asyncio.to_thread(
                ULServiceClient.get_commissioning_dates
            )
            roots = await asyncio.to_thread(OmegaClient().list_passport_roots)
            result = {
                "found": len(roots),
                "imported": 0,
                "reimported": 0,
                "skipped_existing": 0,
                "waiting_for_commissioning": 0,
                "skipped_by_rule": 0,
                "skipped_unknown_model": 0,
                "failed": 0,
                "linked_without_number": 0,
            }
            tree_requests = 0

            async with async_session_maker() as session:
                existing_rows = (
                    await session.execute(
                        select(
                            ProductPassport.id,
                            ProductPassport.omega_root_code,
                            ProductPassport.locomotive_model_id,
                            ProductPassport.product_number,
                            ProductPassport.commissioned_at,
                        )
                    )
                ).all()
                existing_passports = {row.omega_root_code: row for row in existing_rows}
                existing_by_identity = {
                    (row.locomotive_model_id, row.product_number): row
                    for row in existing_rows
                }
                model_rows = (
                    await session.execute(
                        select(
                            LocomotiveModel.id,
                            LocomotiveModel.locomotive_model_name,
                        )
                    )
                ).all()
                model_ids = {
                    row.locomotive_model_name.casefold(): row.id for row in model_rows
                }
                supplier_rows = (
                    await session.execute(select(Supplier.id, Supplier.supplier_name))
                ).all()
                supplier_ids = {row.supplier_name: row.id for row in supplier_rows}
                equipment_rows = (
                    await session.execute(
                        select(
                            Equipment.id,
                            Equipment.equipment_name,
                            Equipment.parent_id,
                            Equipment.supplier_id,
                        )
                    )
                ).all()
                equipment_index: dict[str, list[tuple[int, int | None]]] = {}
                equipment_details: dict[int, tuple[int | None, int | None, str]] = {}
                for row in sorted(equipment_rows, key=lambda item: item.id):
                    equipment_index.setdefault(row.equipment_name, []).append(
                        (row.id, row.parent_id)
                    )
                    equipment_details[row.id] = (
                        row.parent_id,
                        row.supplier_id,
                        row.equipment_name,
                    )
                equipment_match_rows = (
                    await session.execute(
                        select(
                            ProductPassportEquipmentMatch.match_key,
                            ProductPassportEquipmentMatch.equipment_id,
                            ProductPassportEquipmentMatch.supplier_id,
                        )
                    )
                ).all()
                equipment_match_ids = {
                    row.match_key: (row.equipment_id, row.supplier_id)
                    for row in equipment_match_rows
                }
                equipment_serial_match_rows = (
                    await session.execute(
                        select(
                            ProductPassportEquipmentSerialMatch.match_key,
                            ProductPassportEquipmentSerialMatch.serial_length,
                            ProductPassportEquipmentSerialMatch.equipment_id,
                            ProductPassportEquipmentSerialMatch.supplier_id,
                        )
                    )
                ).all()
                equipment_serial_match_ids = {
                    (row.match_key, row.serial_length): (
                        row.equipment_id,
                        row.supplier_id,
                    )
                    for row in equipment_serial_match_rows
                }
                numbered_rows = (
                    await session.execute(
                        select(
                            ProductPassport.locomotive_model_id,
                            ProductPassportNode.tree_name,
                            ProductPassportNode.designation,
                            ProductPassportNode.omega_supplier_raw,
                            ProductPassportNode.manufacturer,
                            func.min(ProductPassportNode.serial_number).label(
                                "serial_number"
                            ),
                            ProductPassportNode.equipment_id,
                            ProductPassportNode.supplier_id,
                        )
                        .join(ProductPassportNode)
                        .where(
                            ProductPassportNode.serial_number.is_not(None),
                            func.btrim(ProductPassportNode.serial_number) != "",
                            ProductPassportNode.equipment_id.is_not(None),
                        )
                        .group_by(
                            ProductPassport.locomotive_model_id,
                            ProductPassportNode.tree_name,
                            ProductPassportNode.designation,
                            ProductPassportNode.omega_supplier_raw,
                            ProductPassportNode.manufacturer,
                            ProductPassportNode.equipment_id,
                            ProductPassportNode.supplier_id,
                        )
                    )
                ).all()
                numbered_links: NumberedPassportLinks = {}
                for row in numbered_rows:
                    node = ProductPassportNode(
                        tree_name=row.tree_name,
                        designation=row.designation,
                        omega_supplier_raw=row.omega_supplier_raw,
                        manufacturer=row.manufacturer,
                        serial_number=row.serial_number,
                        equipment_id=row.equipment_id,
                        supplier_id=row.supplier_id,
                    )
                    ProductPassportEquipmentService.remember_numbered_link(
                        numbered_links, row.locomotive_model_id, node
                    )

            for root in roots:
                try:
                    product_type, model_name, product_number = (
                        ProductPassportSyncService._parse_identity(root)
                    )
                    if not ProductPassportSyncService._is_eligible(
                        model_name, product_number
                    ):
                        result["skipped_by_rule"] += 1
                        continue

                    locomotive_model_id = model_ids.get(model_name.casefold())
                    if locomotive_model_id is None:
                        result["skipped_unknown_model"] += 1
                        logger.warning(
                            "Паспорт %s пропущен: модели %s нет в справочнике",
                            root.omega_name,
                            model_name,
                        )
                        continue

                    commissioned_at = (
                        commissioning_dates.get(
                            (model_name.casefold(), int(product_number))
                        )
                        if product_number.isdigit()
                        else None
                    )
                    if commissioned_at is None:
                        result["waiting_for_commissioning"] += 1
                        continue

                    existing = existing_passports.get(root.omega_root_code)
                    if existing is None:
                        existing = existing_by_identity.get(
                            (locomotive_model_id, product_number)
                        )
                    if existing and existing.commissioned_at is not None:
                        result["skipped_existing"] += 1
                        continue

                    # Старые паспорта уже сохранены, им нужна только дата ввода
                    if existing and ProductPassportSyncService._is_legacy_passport(
                        model_name, product_number
                    ):
                        async with async_session_maker() as session:
                            async with session.begin():
                                saved = await session.get(ProductPassport, existing.id)
                                saved.commissioned_at = commissioned_at
                        result["skipped_existing"] += 1
                        continue

                    if tree_requests:
                        await asyncio.sleep(settings.OMEGA_SYNC_REQUEST_DELAY_SECONDS)
                    omega_passport = await asyncio.to_thread(
                        OmegaClient().get_passport_by_root, root
                    )
                    tree_requests += 1
                    ProductPassportValidator.validate_tree(
                        omega_passport.nodes, omega_passport.omega_root_code
                    )
                    passport = ProductPassportService.create_model(
                        omega_passport=omega_passport,
                        product_type=product_type,
                        locomotive_model_id=locomotive_model_id,
                        product_number=product_number,
                        supplier_ids=supplier_ids,
                        equipment_index=equipment_index,
                        equipment_details=equipment_details,
                        equipment_match_ids=equipment_match_ids,
                        equipment_serial_match_ids=equipment_serial_match_ids,
                        numbered_links=numbered_links,
                    )
                    passport.commissioned_at = commissioned_at
                    async with async_session_maker() as session:
                        async with session.begin():
                            if existing:
                                old_passport = await session.scalar(
                                    select(ProductPassport)
                                    .options(selectinload(ProductPassport.nodes))
                                    .where(ProductPassport.id == existing.id)
                                )
                                ProductPassportSyncService._merge_passport(
                                    old_passport, passport
                                )
                                saved_passport = old_passport
                            else:
                                session.add(passport)
                                saved_passport = passport
                    if existing:
                        result["reimported"] += 1
                    else:
                        result["imported"] += 1
                    for node in saved_passport.nodes:
                        ProductPassportEquipmentService.remember_numbered_link(
                            numbered_links, locomotive_model_id, node
                        )
                    existing_passports[root.omega_root_code] = saved_passport
                except Exception:
                    result["failed"] += 1
                    logger.exception(
                        "Не удалось импортировать паспорт %s", root.omega_name
                    )

            result["linked_without_number"] = (
                await ProductPassportSyncService._link_unnumbered_nodes(numbered_links)
            )
            logger.info(
                "Синхронизация паспортов завершена: найдено %s, импортировано %s, "
                "переимпортировано %s, уже было %s, вне правил %s, "
                "без даты ввода %s, неизвестных моделей %s, ошибок %s, без номера связано %s",
                result["found"],
                result["imported"],
                result["reimported"],
                result["skipped_existing"],
                result["skipped_by_rule"],
                result["waiting_for_commissioning"],
                result["skipped_unknown_model"],
                result["failed"],
                result["linked_without_number"],
            )
            return result

    @staticmethod
    def _is_legacy_passport(model_name: str, product_number: str) -> bool:
        """Сохраняет старые паспорта без повторного чтения дерева Omega"""
        return model_name.casefold() in {"2эс6", "3эс6"} and int(product_number) < 1709

    @staticmethod
    def _merge_passport(saved: ProductPassport, incoming: ProductPassport) -> None:
        """Обновляет изменившиеся узлы по коду Omega, сохраняя их локальные ID"""
        saved.product_type = incoming.product_type
        saved.locomotive_model_id = incoming.locomotive_model_id
        saved.product_number = incoming.product_number
        saved.omega_root_code = incoming.omega_root_code
        saved.omega_name = incoming.omega_name
        saved.commissioned_at = incoming.commissioned_at
        saved.imported_at = datetime.now(timezone.utc)

        current_by_code = {node.omega_code: node for node in saved.nodes}
        merged = []
        source_fields = (
            "parent_omega_code",
            "level",
            "tree_name",
            "full_name",
            "article",
            "designation",
            "serial_number",
            "manufacture_date",
            "install_date",
            "manufacturer",
            "omega_supplier_raw",
            "stockobj_code",
        )
        for node in incoming.nodes:
            current = current_by_code.get(node.omega_code)
            if current is None:
                merged.append(node)
                continue
            identity_fields = (
                "tree_name",
                "designation",
                "serial_number",
                "omega_supplier_raw",
                "manufacturer",
            )
            same_position = all(
                getattr(current, field) == getattr(node, field)
                for field in identity_fields
            )
            for field in source_fields:
                setattr(current, field, getattr(node, field))
            if not same_position or node.equipment_id is not None:
                current.equipment_id = node.equipment_id
            if not same_position or node.supplier_id is not None:
                current.supplier_id = node.supplier_id
            merged.append(current)
        saved.nodes = merged

    @staticmethod
    async def _link_unnumbered_nodes(
        numbered_links: NumberedPassportLinks,
    ) -> int:
        """Дополняет сохранённые безномерные узлы по однозначным номерным записям"""
        linked = 0
        async with async_session_maker() as session:
            async with session.begin():
                rows = (
                    await session.execute(
                        select(
                            ProductPassportNode,
                            ProductPassport.locomotive_model_id,
                        )
                        .join(ProductPassport)
                        .where(
                            ProductPassport.commissioned_at.is_not(None),
                            ProductPassportNode.equipment_id.is_(None),
                            or_(
                                ProductPassportNode.serial_number.is_(None),
                                func.btrim(ProductPassportNode.serial_number) == "",
                            ),
                        )
                    )
                ).all()
                for node, locomotive_model_id in rows:
                    key = (
                        locomotive_model_id,
                        ProductPassportEquipmentService.match_key(
                            node.tree_name,
                            node.designation,
                            node.omega_supplier_raw,
                            node.manufacturer,
                        ),
                    )
                    match = numbered_links.get(key)
                    if match is None:
                        continue
                    equipment_id, supplier_id = match
                    if supplier_id is not None and node.supplier_id not in (
                        None,
                        supplier_id,
                    ):
                        continue
                    node.equipment_id = equipment_id
                    if supplier_id is not None:
                        node.supplier_id = supplier_id
                    linked += 1
        return linked

    @staticmethod
    def _parse_identity(root: OmegaPassportRootData) -> tuple[str, str, str]:
        """Разбирает тип, модель и номер из имени корня Omega"""
        match = re.fullmatch(
            r"(?P<product_type>Электровоз)\s+"
            r"(?P<model>\S+)\s+№\s*(?P<number>[^\s()]+)"
            r"(?:\s*\([^)]*\))?",
            root.omega_name.strip(),
            flags=re.IGNORECASE,
        )
        if not match:
            raise ValueError(f"Не удалось разобрать имя паспорта: {root.omega_name}")
        return (
            match.group("product_type"),
            match.group("model"),
            match.group("number"),
        )

    @staticmethod
    def _is_eligible(model_name: str, product_number: str) -> bool:
        """Проверяет, входит ли паспорт в согласованный диапазон импорта"""
        normalized_model = model_name.casefold()
        if normalized_model in {"2эс8", "3эс8"}:
            return True
        if normalized_model not in {"2эс6", "3эс6"} or not product_number.isdigit():
            return False
        return int(product_number) >= 1534
