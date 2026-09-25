import oracledb
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any

from myapp.config import settings
from myapp.omega.sql_queries import LIST_ROOT_PASSPORTS_SQL, PASSPORT_TREE_SQL
from myapp.schemas.omega import (
    OmegaPassportData,
    OmegaPassportNodeData,
    OmegaPassportRootData,
)


class OmegaClient:
    """Технический клиент для чтения паспортов из Oracle Omega"""

    def list_passport_roots(self) -> list[OmegaPassportRootData]:
        """Возвращает корневые паспорта электровозов из Omega"""
        with self._get_connection() as connection:
            rows = self._fetch_all(connection, LIST_ROOT_PASSPORTS_SQL)
        return [self._to_root(row) for row in rows]

    def get_passport_by_root(self, root: OmegaPassportRootData) -> OmegaPassportData:
        """Получает дерево паспорта по уже найденному корню"""
        with self._get_connection() as connection:
            return self._get_passport_by_root(connection, root)

    @staticmethod
    def _get_passport_by_root(
        connection: Any, root: OmegaPassportRootData
    ) -> OmegaPassportData:
        """Читает дерево паспорта в рамках открытого подключения"""
        rows = OmegaClient._fetch_all(
            connection,
            PASSPORT_TREE_SQL,
            root_code=root.omega_root_code,
        )
        return OmegaPassportData(
            omega_root_code=root.omega_root_code,
            omega_name=root.omega_name,
            nodes=[OmegaClient._to_node(row) for row in rows],
        )

    @staticmethod
    def _to_root(row: Mapping[str, Any]) -> OmegaPassportRootData:
        """Преобразует строку Oracle в краткие данные паспорта"""
        return OmegaPassportRootData(
            omega_root_code=int(row["CODE"]),
            omega_name=str(row["NAME"]),
        )

    @staticmethod
    @contextmanager
    def _get_connection() -> Generator[Any, None, None]:
        """Открывает Oracle-подключение только на время чтения одного паспорта"""
        with oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            dsn=settings.oracle_dsn,
        ) as connection:
            yield connection

    @staticmethod
    def _fetch_all(
        connection: Any, sql: str, **parameters: Any
    ) -> list[dict[str, Any]]:
        """Выполняет запрос и возвращает строки Oracle как словари"""
        with connection.cursor() as cursor:
            cursor.execute(sql, parameters)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor]

    @staticmethod
    def _to_node(row: Mapping[str, Any]) -> OmegaPassportNodeData:
        """Преобразует строку Oracle в схему узла паспорта"""
        return OmegaPassportNodeData(
            omega_code=int(row["CODE"]),
            parent_omega_code=(
                int(row["PARENT_CODE"]) if row["PARENT_CODE"] is not None else None
            ),
            level=int(row["LVL"]),
            tree_name=OmegaClient._required_text(row["TREE_NAME"]),
            full_name=OmegaClient._clean_text(row["FULL_NAME"]),
            peshka=OmegaClient._clean_text(row["PESHKA"]),
            designation=OmegaClient._clean_text(row["DESIGNATION"]),
            serial_number=OmegaClient._clean_text(row["SERIAL_NUMBER"]),
            manufacture_date=OmegaClient._to_date(row["MANUFACTURE_DATE"]),
            install_date=OmegaClient._to_date(row["INSTALL_DATE"]),
            manufacturer=OmegaClient._clean_text(row["MANUFACTURER"]),
            omega_supplier_raw=OmegaClient._clean_text(row["SUPPLIER"]),
            stockobj_code=(
                int(row["STOCKOBJ_CODE"]) if row["STOCKOBJ_CODE"] is not None else None
            ),
        )

    @staticmethod
    def _to_date(value: date | datetime | None) -> date | None:
        """Приводит Oracle DATE, который драйвер может вернуть как datetime"""
        if isinstance(value, datetime):
            return value.date()
        return value

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        """Убирает пробелы и переводы строк по краям значения"""
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    @staticmethod
    def _required_text(value: Any) -> str:
        """Очищает обязательное текстовое значение"""
        cleaned = OmegaClient._clean_text(value)
        if cleaned is None:
            raise ValueError("Узел паспорта не содержит наименование")
        return cleaned
