import asyncio
import logging
import re

from sqlalchemy import select

from myapp.config import settings
from myapp.database.base import async_session_maker
from myapp.models.auxiliaries import LocomotiveModel
from myapp.models.product_passports import ProductPassport
from myapp.omega.client import OmegaClient
from myapp.schemas.omega import OmegaPassportRootData
from myapp.services.product_passport_service import ProductPassportService
from myapp.validators.product_passport_validator import ProductPassportValidator

logger = logging.getLogger(__name__)
_sync_lock = asyncio.Lock()
CURRENT_IMPORT_VERSION = 2


class ProductPassportSyncService:
    """Синхронизация новых паспортов из Omega"""

    @staticmethod
    async def sync_new_passports() -> dict[str, int]:
        """Находит в Omega новые паспорта и сохраняет каждый одной транзакцией"""
        if _sync_lock.locked():
            logger.info("Синхронизация паспортов уже выполняется")
            return {}

        async with _sync_lock:
            roots = await asyncio.to_thread(OmegaClient().list_passport_roots)
            result = {
                "found": len(roots),
                "imported": 0,
                "reimported": 0,
                "skipped_existing": 0,
                "skipped_by_rule": 0,
                "skipped_unknown_model": 0,
                "failed": 0,
            }
            tree_requests = 0

            async with async_session_maker() as session:
                existing_rows = (
                    await session.execute(
                        select(
                            ProductPassport.id,
                            ProductPassport.omega_root_code,
                            ProductPassport.import_version,
                        )
                    )
                ).all()
                existing_passports = {row.omega_root_code: row for row in existing_rows}
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

            for root in roots:
                existing = existing_passports.get(root.omega_root_code)
                if existing and existing.import_version >= CURRENT_IMPORT_VERSION:
                    result["skipped_existing"] += 1
                    continue

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
                    )
                    async with async_session_maker() as session:
                        async with session.begin():
                            if existing:
                                old_passport = await session.get(
                                    ProductPassport, existing.id
                                )
                                await session.delete(old_passport)
                                await session.flush()
                            session.add(passport)
                    if existing:
                        result["reimported"] += 1
                    else:
                        result["imported"] += 1
                    existing_passports[root.omega_root_code] = passport
                except Exception:
                    result["failed"] += 1
                    logger.exception(
                        "Не удалось импортировать паспорт %s", root.omega_name
                    )

            logger.info(
                "Синхронизация паспортов завершена: найдено %s, импортировано %s, "
                "переимпортировано %s, уже было %s, вне правил %s, "
                "неизвестных моделей %s, ошибок %s",
                result["found"],
                result["imported"],
                result["reimported"],
                result["skipped_existing"],
                result["skipped_by_rule"],
                result["skipped_unknown_model"],
                result["failed"],
            )
            return result

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
