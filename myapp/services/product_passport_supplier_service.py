import re

from myapp.constants.product_passport_supplier_constants import (
    SUPPLIER_NAMES,
    MANUFACTURER_IF_NO_SUPPLIER,
    MANUFACTURER_OVERRIDES,
)
from myapp.models.product_passports import ProductPassportNode


class ProductPassportSupplierService:
    """Определяет поставщика узла паспорта по данным Omega"""

    @staticmethod
    def _key(value: str | None) -> str:
        return " ".join((value or "").upper().split())

    @classmethod
    def is_26t_amortizer(cls, tree_name: str, designation: str | None) -> bool:
        """Проверяет обозначение амортизатора 26Т"""
        return (
            "АМОРТИЗАТОР" in cls._key(tree_name)
            and cls._key(designation) == "26Т.081.02.000"
        )

    @classmethod
    def resolve_name(
        cls,
        locomotive_model_id: int,
        tree_name: str,
        supplier: str | None,
        manufacturer: str | None,
        designation: str | None = None,
        serial_number: str | None = None,
    ) -> str | None:
        """Возвращает имя поставщика из справочника для 2ЭС6 и 3ЭС6"""
        if locomotive_model_id not in (1, 6):
            return None
        if "АМОРТИЗАТОР" in cls._key(tree_name):
            if re.search(r"5BV002[PР]", (designation or "").upper()):
                return "ООО «ПААЗ»"
            serial = (serial_number or "").strip()
            if serial.isdecimal() and len(serial) == 7:
                return "ООО «ПААЗ»"
            if cls.is_26t_amortizer(tree_name, designation):
                if serial.isdecimal():
                    if len(serial) == 5:
                        return "ООО «ТрансЭлКон»"
                    if len(serial) < 5:
                        return "ООО «Спецкомплектсервис»"
            return None

        supplier_key = cls._key(supplier)
        manufacturer_key = cls._key(manufacturer)

        if (
            not supplier_key
            and cls._key(tree_name).startswith("БАЛЛОН 25-150У")
            and manufacturer_key
            == "ООО УРАЛЬСКИЙ ЗАВОД ГАЗОВОГО И ПРОТИВОПОЖАРНОГО ОБОРУДОВАНИЯ"
        ):
            return "ООО «Пожарные системы»"

        if supplier_key == "ПТСК ООО":
            return "ООО «Лаборатория радиосвязи»"

        if (
            supplier_key == "ТЯГОВЫЕ КОМПОНЕНТЫ ООО"
            and manufacturer_key == "0112"
            and cls._key(tree_name) == "ПРЕОБРАЗОВАТЕЛЬ НАПРЯЖЕНИЯ ПНКВ-3"
        ):
            return "ООО «НПО САУТ»"

        override = MANUFACTURER_OVERRIDES.get((supplier_key, manufacturer_key))
        if override:
            return override

        if not supplier_key:
            return MANUFACTURER_IF_NO_SUPPLIER.get(manufacturer_key)

        return SUPPLIER_NAMES.get(supplier_key)

    @classmethod
    def resolve_id(
        cls,
        locomotive_model_id: int,
        node: ProductPassportNode,
        supplier_ids: dict[str, int],
    ) -> int | None:
        """Возвращает ID поставщика без изменения изготовителя и сырых данных Omega"""
        name = cls.resolve_name(
            locomotive_model_id,
            node.tree_name,
            node.omega_supplier_raw,
            node.manufacturer,
            node.designation,
            node.serial_number,
        )
        return supplier_ids.get(name) if name else None
