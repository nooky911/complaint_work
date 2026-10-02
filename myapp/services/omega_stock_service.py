"""Сервис просмотра складских документов Omega"""

import asyncio
from datetime import date

from myapp.config import settings
from myapp.omega.stock_client import OmegaStockClient


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
    ) -> list[dict]:
        if date_from and date_to and date_from > date_to:
            raise ValueError("Начальная дата не может быть позже конечной")
        allowed_ids = await self._warehouse_ids(kind, warehouse_ids)
        return await asyncio.to_thread(
            self.client.list_documents,
            kind,
            allowed_ids,
            number,
            date_from,
            date_to,
            offset,
            limit,
        )

    async def _document_available(self, kind: str, document_id: int) -> bool:
        warehouse_ids = await self._warehouse_ids(kind)
        return await asyncio.to_thread(
            self.client.document_exists, kind, document_id, warehouse_ids
        )

    async def list_items(self, kind: str, document_id: int) -> list[dict] | None:
        if not await self._document_available(kind, document_id):
            return None
        return await asyncio.to_thread(self.client.list_items, kind, document_id)

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
