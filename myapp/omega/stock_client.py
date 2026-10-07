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
    DOCUMENT_FILTER_COLUMNS,
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
        column_filters: dict[str, dict[str, Any]] | None = None,
        sort_column: str | None = None,
        sort_direction: str = "desc",
        warehouse_names: dict[int, str] | None = None,
        supplier_names: dict[str, str] | None = None,
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

        conditions = []
        date_column = "ACCOUNTING_DATE" if kind == "receipts" else "DOCUMENT_DATE"
        if number:
            conditions.append('INSTR(d."NUMBER", :p_number) > 0')
            parameters["p_number"] = number.strip()
        if date_from:
            conditions.append(f'd."{date_column}" >= :p_date_from')
            parameters["p_date_from"] = datetime.combine(date_from, time.min)
        if date_to:
            conditions.append(f'd."{date_column}" < :p_date_to')
            parameters["p_date_to"] = datetime.combine(
                date_to + timedelta(days=1), time.min
            )
        conditions.extend(self._column_conditions(kind, column_filters or {}, parameters))
        base_sql = self._document_query(
            kind, warehouse_binds, warehouse_ids, warehouse_names or {},
            supplier_names or {}, parameters,
        )
        where = " AND ".join(conditions) if conditions else "1=1"
        if sort_column is None:
            sort_expression = f'd."{date_column}"'
        else:
            sort_expression = f'd."{sort_column.upper()}"'
            if DOCUMENT_FILTER_COLUMNS[kind][sort_column] == "text":
                sort_expression = f"UPPER(TRIM({sort_expression}))"
        direction = "ASC" if sort_direction == "asc" else "DESC"
        sql = f"""
            SELECT d.* FROM ({base_sql}) d
            WHERE {where}
            ORDER BY {sort_expression} {direction} NULLS LAST, d.DOCUMENT_ID DESC
            OFFSET :p_offset ROWS FETCH NEXT :p_limit ROWS ONLY
        """
        with self._get_connection() as connection:
            return self._fetch_all(connection, sql, **parameters)

    @staticmethod
    def _filter_expression(kind: str, column: str) -> str:
        column_type = DOCUMENT_FILTER_COLUMNS[kind][column]
        expression = f'd."{column.upper()}"'
        if column_type == "date":
            return f"TO_CHAR({expression}, 'YYYY-MM-DD')"
        if column_type == "datetime":
            return f"TO_CHAR({expression}, 'YYYY-MM-DD\"T\"HH24:MI')"
        if column_type == "files":
            return f"TO_CHAR({expression})"
        return f"TRIM({expression})"

    @staticmethod
    def _document_query(
        kind: str,
        warehouse_binds: list[str],
        warehouse_ids: list[int],
        warehouse_names: dict[int, str],
        supplier_names: dict[str, str],
        parameters: dict[str, Any],
    ) -> str:
        """Подставляет имена из нашего справочника до фильтрации и сортировки Oracle."""
        warehouse_alias = "sender" if kind == "inplant" else "w"
        warehouse_raw = f"{warehouse_alias}.SIGN || ' - ' || {warehouse_alias}.NAME"
        warehouse_cases = []
        for index, warehouse_id in enumerate(warehouse_ids):
            if warehouse_id in warehouse_names:
                key = f"p_warehouse_name_{index}"
                parameters[key] = warehouse_names[warehouse_id]
                warehouse_cases.append(f"WHEN {warehouse_binds[index]} THEN :{key}")
        warehouse_expr = (
            f"CASE {warehouse_alias}.CODE {' '.join(warehouse_cases)} "
            f"ELSE {warehouse_raw} END"
            if warehouse_cases else warehouse_raw
        )

        supplier_cases = []
        if kind != "inplant":
            for index, (omega_name, display_name) in enumerate(supplier_names.items()):
                raw_key = f"p_supplier_raw_{index}"
                display_key = f"p_supplier_name_{index}"
                parameters[raw_key] = omega_name
                parameters[display_key] = display_name
                supplier_cases.append(f"WHEN :{raw_key} THEN :{display_key}")
        supplier_expr = (
            f"CASE e.NAME {' '.join(supplier_cases)} ELSE e.NAME END"
            if supplier_cases else "e.NAME"
        )
        recipient_expr = "receiver.SIGN || ' - ' || receiver.NAME"
        if kind == "inplant":
            parameters["p_usoe_recipient"] = "РЕК_УСОЭ - Склад рекл. оборуд-ия"
            recipient_expr = ":p_usoe_recipient"

        return DOCUMENT_QUERIES[kind].format(
            warehouses=", ".join(warehouse_binds),
            warehouse_expr=warehouse_expr,
            supplier_expr=supplier_expr,
            recipient_expr=recipient_expr,
        )

    def _column_conditions(
        self,
        kind: str,
        filters: dict[str, dict[str, Any]],
        parameters: dict[str, Any],
        except_column: str | None = None,
    ) -> list[str]:
        conditions = []
        for column, selection in filters.items():
            if column == except_column:
                continue
            expression = self._filter_expression(kind, column)
            values = selection["values"]
            has_empty = None in values
            actual_values = [value for value in values if value is not None]
            mode = selection["mode"]
            if mode == "include" and not values:
                conditions.append("1=0")
                continue
            if mode == "exclude" and not values:
                continue
            parts = []
            for start in range(0, len(actual_values), 500):
                binds = []
                for index, value in enumerate(actual_values[start:start + 500], start):
                    key = f"p_filter_{column}_{index}"
                    parameters[key] = value
                    binds.append(f":{key}")
                parts.append(f"{expression} IN ({', '.join(binds)})")
            matches = " OR ".join(parts)
            if mode == "include":
                if has_empty:
                    parts.append(f"{expression} IS NULL")
                conditions.append(f"({' OR '.join(parts)})")
            else:
                if matches:
                    condition = f"NOT ({matches})"
                    if not has_empty:
                        condition = f"({expression} IS NULL OR {condition})"
                else:
                    condition = "1=1"
                if has_empty:
                    condition = f"({expression} IS NOT NULL AND {condition})"
                conditions.append(condition)
        return conditions

    def list_filter_options(
        self,
        kind: str,
        warehouse_ids: list[int],
        column: str,
        filters: dict[str, dict[str, Any]],
        warehouse_names: dict[int, str] | None = None,
        supplier_names: dict[str, str] | None = None,
    ) -> list[str | None]:
        """Возвращает значения колонки среди документов, прошедших остальные фильтры."""
        if not warehouse_ids:
            return []
        parameters = {}
        binds = []
        for index, warehouse_id in enumerate(warehouse_ids):
            key = f"p_warehouse_{index}"
            parameters[key] = warehouse_id
            binds.append(f":{key}")
        base_sql = self._document_query(
            kind, binds, warehouse_ids, warehouse_names or {},
            supplier_names or {}, parameters,
        )
        conditions = self._column_conditions(kind, filters, parameters, column)
        where = " AND ".join(conditions) if conditions else "1=1"
        expression = self._filter_expression(kind, column)
        sql = f"""
            SELECT DISTINCT {expression} AS FILTER_VALUE
            FROM ({base_sql}) d
            WHERE {where}
            ORDER BY FILTER_VALUE NULLS FIRST
        """
        with self._get_connection() as connection:
            return [row["filter_value"] for row in self._fetch_all(connection, sql, **parameters)]

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
