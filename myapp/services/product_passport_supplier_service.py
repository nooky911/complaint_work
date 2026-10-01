import re

from myapp.constants.product_passport_supplier_constants import (
    SUPPLIER_NAMES,
    MANUFACTURER_IF_NO_SUPPLIER,
    MANUFACTURER_OVERRIDES,
)
from myapp.models.product_passports import ProductPassportNode


class ProductPassportSupplierService:
    """Определяет поставщика узла паспорта по Omega и классификатору"""

    @staticmethod
    def _key(value: str | None) -> str:
        return " ".join((value or "").upper().split())

    @staticmethod
    def _entity_key(value: str | None) -> str:
        return "".join(
            char
            for char in (value or "").upper().replace("Ё", "Е")
            if char.isalnum()
        )

    @classmethod
    def _manufacturer_id(
        cls, manufacturer: str | None, supplier_ids: dict[str, int]
    ) -> int | None:
        """Находит изготовителя в общем справочнике поставщиков"""
        manufacturer_key = cls._key(manufacturer)
        mapped_name = MANUFACTURER_IF_NO_SUPPLIER.get(
            manufacturer_key
        ) or SUPPLIER_NAMES.get(manufacturer_key)
        if mapped_name and mapped_name in supplier_ids:
            return supplier_ids[mapped_name]

        entity_key = cls._entity_key(manufacturer)
        if not entity_key:
            return None
        matches = {
            supplier_id
            for name, supplier_id in supplier_ids.items()
            if cls._entity_key(name) == entity_key
        }
        return matches.pop() if len(matches) == 1 else None

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

        if cls._key(tree_name).startswith(("АНТЕННА АЛ2/160", "АНТЕННА АЛ3/800")):
            return supplier_ids.get("ООО «НПО САУТ»")

        if (designation or "").upper().replace(" ", "") == "3506/177.787-2LS":
            return supplier_ids.get("ООО НЭМЗ «ТАЙРА»")

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

        supplier_id = supplier_ids.get(SUPPLIER_NAMES.get(supplier_key))
        if supplier_id is not None:
            return supplier_id
        return cls._manufacturer_id(manufacturer, supplier_ids)

    @classmethod
    def resolve_8_id(
        cls,
        node: ProductPassportNode,
        supplier_ids: dict[str, int],
        equipment_details: dict[int, tuple[int | None, int | None, str]],
    ) -> int | None:
        """Определяет поставщика для паспортов 2ЭС8 и 3ЭС8"""
        name = cls._key(node.tree_name)
        if name == "КОМПЛЕКТ ТЯГОВОГО ОБОРУДОВАНИЯ КТО" and (
            node.designation or node.serial_number
        ):
            return supplier_ids.get("ООО «Тяговые компоненты»")
        if name.startswith("МИКРОТЕЛЕФОННАЯ ТРУБКА МТТ2"):
            return supplier_ids.get("ООО «Лаборатория радиосвязи»")
        if name == "КОНДИЦИОНЕР":
            return supplier_ids.get("ООО «Горизонт»")
        if (
            "МАНОМЕТР" in name
            and "МП" in name
            and (node.designation or "").upper() == "5ШО.283.043"
        ):
            return supplier_ids.get("ОАО «Манотомь»")
        if name.startswith("ШЛЮЗ 230Д.70-10") or name.startswith("МОДЕМ - РУТП"):
            return supplier_ids.get("АО «МТЗ ТРАНСМАШ»")
        if name.startswith("МОДУЛЬ МППМ-160Д") or name.startswith(
            "МОДУЛЬ ПИТАНИЯ МПСВ1-110Г"
        ):
            return supplier_ids.get("ООО «Лаборатория радиосвязи»")
        if name.startswith(
            ("ОСЬ ", "КОЛЕСНЫЙ ЦЕНТР", "КОЛЕСО ЗУБЧАТОЕ", "ШЕСТЕРНЯ 11103")
        ):
            return supplier_ids.get("ООО «Уральские локомотивы»")

        ancestry = []
        equipment_supplier_id = None
        equipment_id = node.equipment_id
        while equipment_id is not None and equipment_id in equipment_details:
            parent_id, current_supplier_id, equipment_name = equipment_details[
                equipment_id
            ]
            ancestry.append(equipment_name)
            if equipment_supplier_id is None:
                equipment_supplier_id = current_supplier_id
            equipment_id = parent_id

        if "Система_микроклимата" in ancestry or any(
            equipment_name in {"БУНСм_110DC_4", "ГИС_5Г", "11103.А.81.800.000"}
            for equipment_name in ancestry
        ):
            return supplier_ids.get("ООО «Горизонт»")

        supplier_key = cls._key(node.omega_supplier_raw)
        if any(
            fragment in supplier_key
            for fragment in ("САУТ", "ГОРИЗОНТ", "ТЯГОВЫЕ КОМПОНЕНТЫ")
        ):
            return supplier_ids.get("ООО «Тяговые компоненты»")

        if equipment_supplier_id is not None:
            if equipment_supplier_id in {
                supplier_ids.get("ООО «НПО САУТ»"),
                supplier_ids.get("ООО «Горизонт»"),
            }:
                return supplier_ids.get("ООО «Тяговые компоненты»")
            return equipment_supplier_id

        target = SUPPLIER_NAMES.get(supplier_key)
        if target:
            supplier_id = supplier_ids.get(target)
            if supplier_id is not None:
                return supplier_id
        manufacturer_supplier_id = cls._manufacturer_id(
            node.manufacturer, supplier_ids
        )
        if manufacturer_supplier_id is not None and manufacturer_supplier_id in {
            supplier_ids.get("ООО «НПО САУТ»"),
            supplier_ids.get("ООО «Горизонт»"),
        }:
            return supplier_ids.get("ООО «Тяговые компоненты»")
        return manufacturer_supplier_id
