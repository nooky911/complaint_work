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
    def resolve_id(
        cls,
        locomotive_model_id: int,
        node: ProductPassportNode,
        supplier_ids: dict[str, int],
    ) -> int | None:
        """Возвращает ID поставщика по данным Omega"""
        if locomotive_model_id not in (1, 6):
            return None
        tree_name = node.tree_name
        supplier = node.omega_supplier_raw
        manufacturer = node.manufacturer
        designation = node.designation
        serial_number = node.serial_number

        if cls._key(tree_name).startswith("ОГРАНИЧИТЕЛЬ ПЕРЕНАПРЯЖЕНИЙ"):
            maker = cls._key(manufacturer)
            if "ЭКИ" in maker:
                return supplier_ids.get("ОАО «НИИ «ЭКИ»")
            if "ЗАИ" in maker and (serial_number or "").strip().isdecimal():
                if len((serial_number or "").strip()) < 6:
                    return supplier_ids.get("АО «НИИ «ЗАИ»")
                return supplier_ids.get("ОАО «НИИ «ЗАИ»")
            return None
        if "АМОРТИЗАТОР" in cls._key(tree_name):
            if re.search(r"5BV002[PР]", (designation or "").upper()):
                return supplier_ids.get("ООО «ПААЗ»")
            serial = (serial_number or "").strip()
            if serial.isdecimal() and len(serial) == 7:
                return supplier_ids.get("ООО «ПААЗ»")
            if cls.is_26t_amortizer(tree_name, designation) or (
                not designation
                and cls._key(tree_name)
                in {"АМОРТИЗАТОР ЛЕВЫЙ, КП4", "АМОРТИЗАТОР ПРАВЫЙ, КП3"}
                and cls._key(supplier) == "КОМПАНИЯ ДЕМПФЕРСЕРВИС ООО"
            ):
                if serial.isdecimal():
                    if len(serial) == 5:
                        return supplier_ids.get("ООО «ТрансЭлКон»")
                    if len(serial) < 5:
                        return supplier_ids.get("ООО «Спецкомплектсервис»")
            return None

        supplier_key = cls._key(supplier)
        manufacturer_key = cls._key(manufacturer)

        if (
            not supplier_key
            and cls._key(tree_name).startswith("БАЛЛОН 25-150У")
            and manufacturer_key
            == "ООО УРАЛЬСКИЙ ЗАВОД ГАЗОВОГО И ПРОТИВОПОЖАРНОГО ОБОРУДОВАНИЯ"
        ):
            return supplier_ids.get("ООО «Пожарные системы»")

        if supplier_key == "ПТСК ООО":
            return supplier_ids.get("ООО «Лаборатория радиосвязи»")

        if (
            supplier_key == "ТЯГОВЫЕ КОМПОНЕНТЫ ООО"
            and manufacturer_key == "0112"
            and cls._key(tree_name) == "ПРЕОБРАЗОВАТЕЛЬ НАПРЯЖЕНИЯ ПНКВ-3"
        ):
            return supplier_ids.get("ООО «НПО САУТ»")

        override = MANUFACTURER_OVERRIDES.get((supplier_key, manufacturer_key))
        if override:
            return supplier_ids.get(override)

        if not supplier_key:
            return supplier_ids.get(MANUFACTURER_IF_NO_SUPPLIER.get(manufacturer_key))

        return supplier_ids.get(SUPPLIER_NAMES.get(supplier_key))
