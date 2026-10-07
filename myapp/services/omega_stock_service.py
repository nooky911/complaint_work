"""Сервис просмотра складских документов Omega"""

import asyncio
import re
from datetime import date

from sqlalchemy import select

from myapp.config import settings
from myapp.database.base import async_session_maker
from myapp.models.auxiliaries import OmegaStockSupplierName, RegionalCenter, Supplier
from myapp.omega.stock_client import OmegaStockClient
from myapp.omega.stock_queries import DOCUMENT_FILTER_COLUMNS
from myapp.schemas.omega_stock import OmegaStockColumnFilter


class OmegaStockService:
    """Проверяет область просмотра и читает актуальные данные из Omega"""

    def __init__(self) -> None:
        self.client = OmegaStockClient()

    @staticmethod
    def _check_connection() -> None:
        if not all(
            (
                settings.ORACLE_HOST,
                settings.ORACLE_PORT,
                settings.ORACLE_SERVICE,
                settings.ORACLE_USER,
                settings.ORACLE_PASSWORD,
            )
        ):
            raise RuntimeError("Подключение к Omega не настроено")

    async def list_warehouses(self, kind: str) -> list[dict]:
        self._check_connection()
        return await asyncio.to_thread(self.client.list_warehouses, kind)

    @staticmethod
    async def _display_names() -> tuple[dict[str, str], dict[int, str]]:
        """Читает соответствия одним запросом к каждому своему справочнику."""
        async with async_session_maker() as session:
            suppliers = await session.execute(
                select(
                    OmegaStockSupplierName.omega_name,
                    Supplier.supplier_name,
                    OmegaStockSupplierName.display_name,
                ).join(Supplier, Supplier.id == OmegaStockSupplierName.supplier_id)
            )
            centers = await session.execute(
                select(RegionalCenter.regional_center_name)
            )
        supplier_names = {
            omega: override or name for omega, name, override in suppliers
        }
        center_names = {}
        for (name,) in centers:
            match = re.match(r"РЦ\s*(\d+)\b", name, re.IGNORECASE)
            if match:
                center_names[int(match.group(1))] = name
        return supplier_names, center_names

    @staticmethod
    def _warehouse_names(
        warehouses: list[dict], centers: dict[int, str], kind: str
    ) -> dict[int, str]:
        result = {}
        for warehouse in warehouses:
            sign = re.sub(r"\s+", "", warehouse["sign"].upper())
            if "УСОЭ" in sign:
                result[warehouse["id"]] = (
                    "ГР_УСОЭ - Склад годного оборуд-ия"
                    if kind == "receipts" else "РЕК_УСОЭ - Склад рекл. оборуд-ия"
                )
                continue
            match = re.search(r"РЦ\D*(\d+)$", sign)
            if match and int(match.group(1)) in centers:
                result[warehouse["id"]] = centers[int(match.group(1))]
        return result

    @staticmethod
    def _center_by_sign(sign: str, centers: dict[int, str]) -> str | None:
        normalized = re.sub(r"\s+", "", sign.upper())
        match = re.search(r"РЦ\D*(\d+)$", normalized)
        return centers.get(int(match.group(1))) if match else None

    async def _warehouse_ids(
        self, kind: str, selected_ids: list[int] | None = None
    ) -> list[int]:
        warehouses = await self.list_warehouses(kind)
        allowed_ids = {warehouse["id"] for warehouse in warehouses}
        if selected_ids is not None and not set(selected_ids) <= allowed_ids:
            raise ValueError("Выбранный склад не относится к этому виду документов")
        return sorted(set(selected_ids)) if selected_ids is not None else sorted(allowed_ids)

    async def list_documents(
        self,
        kind: str,
        warehouse_ids: list[int] | None,
        number: str | None,
        date_from: date | None,
        date_to: date | None,
        offset: int,
        limit: int,
        column_filters: dict[str, OmegaStockColumnFilter] | None = None,
        sort_column: str | None = None,
        sort_direction: str = "desc",
    ) -> list[dict]:
        if date_from and date_to and date_from > date_to:
            raise ValueError("Начальная дата не может быть позже конечной")
        if sort_column is not None and sort_column not in DOCUMENT_FILTER_COLUMNS[kind]:
            raise ValueError(f"Неизвестная колонка сортировки: {sort_column}")
        if sort_direction not in ("asc", "desc"):
            raise ValueError("Неизвестное направление сортировки")
        warehouses = await self.list_warehouses(kind)
        allowed = {warehouse["id"] for warehouse in warehouses}
        if warehouse_ids is not None and not set(warehouse_ids) <= allowed:
            raise ValueError("Выбранный склад не относится к этому виду документов")
        allowed_ids = sorted(set(warehouse_ids)) if warehouse_ids is not None else sorted(allowed)
        supplier_names, centers = await self._display_names()
        display_warehouses = self._warehouse_names(warehouses, centers, kind)
        filters = self._validated_filters(kind, column_filters)
        return await asyncio.to_thread(
            self.client.list_documents,
            kind,
            allowed_ids,
            number,
            date_from,
            date_to,
            offset,
            limit,
            filters,
            sort_column,
            sort_direction,
            display_warehouses,
            supplier_names,
        )

    @staticmethod
    def _validated_filters(
        kind: str, filters: dict[str, OmegaStockColumnFilter] | None
    ) -> dict[str, dict]:
        result = {}
        for column, selection in (filters or {}).items():
            if column not in DOCUMENT_FILTER_COLUMNS[kind]:
                raise ValueError(f"Неизвестная колонка фильтра: {column}")
            values = selection.values
            if any(value is not None and len(value) > 1000 for value in values):
                raise ValueError("Значение фильтра слишком длинное")
            if DOCUMENT_FILTER_COLUMNS[kind][column] == "files" and any(
                value not in (None, "0", "1") for value in values
            ):
                raise ValueError("Недопустимое значение фильтра файлов")
            result[column] = {"mode": selection.mode, "values": values}
        return result

    async def list_filter_options(
        self,
        kind: str,
        column: str,
        column_filters: dict[str, OmegaStockColumnFilter],
    ) -> list[str | None]:
        if column not in DOCUMENT_FILTER_COLUMNS[kind]:
            raise ValueError(f"Неизвестная колонка фильтра: {column}")
        filters = self._validated_filters(kind, column_filters)
        warehouses = await self.list_warehouses(kind)
        allowed_ids = sorted({warehouse["id"] for warehouse in warehouses})
        supplier_names, centers = await self._display_names()
        return await asyncio.to_thread(
            self.client.list_filter_options, kind, allowed_ids, column, filters,
            self._warehouse_names(warehouses, centers, kind), supplier_names,
        )

    async def _document_available(self, kind: str, document_id: int) -> bool:
        warehouse_ids = await self._warehouse_ids(kind)
        return await asyncio.to_thread(
            self.client.document_exists, kind, document_id, warehouse_ids
        )

    async def list_items(self, kind: str, document_id: int) -> list[dict] | None:
        if not await self._document_available(kind, document_id):
            return None
        items = await asyncio.to_thread(self.client.list_items, kind, document_id)
        if kind == "inplant":
            _, centers = await self._display_names()
            for item in items:
                sign = item.get("sender_sign")
                if sign:
                    item["sender_warehouse"] = (
                        self._center_by_sign(sign, centers)
                        or item["sender_warehouse"]
                    )
        return items

    async def list_files(self, kind: str, document_id: int) -> list[dict] | None:
        if not await self._document_available(kind, document_id):
            return None
        return await asyncio.to_thread(self.client.list_files, document_id)

    async def get_file(
        self, kind: str, document_id: int, file_id: int
    ) -> bytes | None:
        if not await self._document_available(kind, document_id):
            return None
        return await asyncio.to_thread(self.client.get_file, document_id, file_id)
