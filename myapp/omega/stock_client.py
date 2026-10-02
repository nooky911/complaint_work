"""Чтение складских документов и вложений из Oracle Omega"""

import bz2
import re
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from typing import Any, Generator

import oracledb

from myapp.config import settings
from myapp.constants.omega_stock_constants import (
    OMEGA_STOCK_RC_NUMBERS,
    OMEGA_STOCK_WITH_USOE,
)
from myapp.omega.stock_queries import (
    DETAIL_QUERIES,
    DOCUMENT_QUERIES,
    DOCUMENT_TABLES,
    FILE_EXISTS_SQL,
    FILE_PARTS_SQL,
    FILES_SQL,
    WAREHOUSES_SQL,
)


class OmegaStockClient:
    """Получает только разрешённые для просмотра документы Omega"""

    @staticmethod
    @contextmanager
    def _get_connection() -> Generator[Any, None, None]:
        """Открывает подключение к Omega на время одного чтения"""
        with oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=settings.oracle_dsn,
        ) as connection:
            connection.call_timeout = 30000
            yield connection

    @staticmethod
    def _fetch_all(connection: Any, sql: str, **parameters: Any) -> list[dict[str, Any]]:
        """Возвращает строки запроса как словари с именами колонок"""
        with connection.cursor() as cursor:
            cursor.execute(sql, parameters)
            names = [column[0].lower() for column in cursor.description]
            return [dict(zip(names, row, strict=True)) for row in cursor]

    @staticmethod
    def _warehouse_allowed(kind: str, sign: str) -> bool:
        """Проверяет склад по списку РЦ для выбранного вида документов"""
        normalized = re.sub(r"\s+", "", sign.upper())
        prefix = "ГР_" if kind == "receipts" else "РЕК_"
        if not normalized.startswith(prefix):
            return False
        if "УСОЭ" in normalized:
            return kind in OMEGA_STOCK_WITH_USOE
        match = re.search(r"РЦ\D*(\d+)$", normalized)
        return bool(match and int(match.group(1)) in OMEGA_STOCK_RC_NUMBERS[kind])

    def list_warehouses(self, kind: str) -> list[dict[str, Any]]:
        """Возвращает склады РЦ и УСОЭ из справочника Omega"""
        with self._get_connection() as connection:
            rows = self._fetch_all(connection, WAREHOUSES_SQL)
        return [
            {"id": int(row["code"]), "sign": row["sign"], "name": row["name"]}
            for row in rows
            if row["sign"] and self._warehouse_allowed(kind, row["sign"])
        ]

    def list_documents(
        self,
        kind: str,
        warehouse_ids: list[int],
        number: str | None,
        date_from: date | None,
        date_to: date | None,
        offset: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Читает страницу документов по складам и датам"""
        if not warehouse_ids:
            return []

        parameters: dict[str, Any] = {"p_offset": offset, "p_limit": limit}
        warehouse_binds = []
        for index, warehouse_id in enumerate(warehouse_ids):
            key = f"p_warehouse_{index}"
            parameters[key] = warehouse_id
            warehouse_binds.append(f":{key}")

        alias = "o" if kind == "receipts" else "i"
        number_column = "ORDNUM" if kind == "receipts" else "INVOICENUM"
        date_column = "ORDDATE" if kind == "receipts" else "INVOICEDATE"
        filters = []
        if number:
            filters.append(f"AND INSTR({alias}.{number_column}, :p_number) > 0")
            parameters["p_number"] = number.strip()
        if date_from:
            filters.append(f"AND {alias}.{date_column} >= :p_date_from")
            parameters["p_date_from"] = datetime.combine(date_from, time.min)
        if date_to:
            filters.append(f"AND {alias}.{date_column} < :p_date_to")
            parameters["p_date_to"] = datetime.combine(
                date_to + timedelta(days=1), time.min
            )

        sql = DOCUMENT_QUERIES[kind].format(
            warehouses=", ".join(warehouse_binds),
            filters="\n          ".join(filters),
        )
        with self._get_connection() as connection:
            return self._fetch_all(connection, sql, **parameters)

    def document_exists(self, kind: str, document_id: int, warehouse_ids: list[int]) -> bool:
        """Проверяет принадлежность документа доступному складу"""
        if not warehouse_ids:
            return False
        table = DOCUMENT_TABLES[kind]
        warehouse_column = "WSCODE" if kind == "receipts" else "WSSENDERCODE"
        parameters = {"p_document_id": document_id}
        binds = []
        for index, warehouse_id in enumerate(warehouse_ids):
            key = f"p_warehouse_{index}"
            parameters[key] = warehouse_id
            binds.append(f":{key}")
        recipient_filter = ""
        if kind == "inplant":
            recipient_filter = """
                AND EXISTS (
                    SELECT 1 FROM OMP_ADM.DIVISIONOBJ receiver
                    WHERE receiver.CODE = d.WSADDRESSECODE
                      AND receiver.SIGN = 'РЕК_УСОЭ'
                )
            """
        sql = f"""
            SELECT 1 FROM OMP_ADM.{table} d
            WHERE d.CODE = :p_document_id
              AND NVL(d.ISDELETED, 0) = 0
              AND d.{warehouse_column} IN ({', '.join(binds)})
              {recipient_filter}
        """
        with self._get_connection() as connection:
            return bool(self._fetch_all(connection, sql, **parameters))

    def list_items(self, kind: str, document_id: int) -> list[dict[str, Any]]:
        """Возвращает строки состава документа"""
        with self._get_connection() as connection:
            return self._fetch_all(
                connection,
                DETAIL_QUERIES[kind],
                p_document_id=document_id,
            )

    def list_files(self, document_id: int) -> list[dict[str, Any]]:
        """Возвращает список вложений документа"""
        with self._get_connection() as connection:
            return self._fetch_all(connection, FILES_SQL, p_document_id=document_id)

    def get_file(self, document_id: int, file_id: int) -> bytes | None:
        """Собирает файл из частей и распаковывает его при необходимости"""
        with self._get_connection() as connection:
            files = self._fetch_all(
                connection,
                FILE_EXISTS_SQL,
                p_document_id=document_id,
                p_file_id=file_id,
            )
            if not files:
                return None

            with connection.cursor() as cursor:
                cursor.execute(
                    FILE_PARTS_SQL,
                    p_file_id=file_id,
                )
                chunks = []
                for _, compressed, lob in cursor:
                    stored = lob.read()
                    if compressed == 1:
                        if (
                            len(stored) < 11
                            or int.from_bytes(stored[4:8], "little") != 0x12345678
                            or stored[8:11] != b"BZh"
                        ):
                            raise RuntimeError("Неизвестный формат сжатия файла Omega")
                        expected_size = int.from_bytes(stored[:4], "little")
                        content = bz2.decompress(stored[8:])
                        if len(content) != expected_size:
                            raise RuntimeError("Размер файла Omega не совпадает с заголовком")
                    else:
                        content = stored
                    chunks.append(content)

        if not chunks:
            return None
        return b"".join(chunks)
