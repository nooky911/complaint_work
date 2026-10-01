import hashlib
import json
import re

from myapp.constants.product_passport_equipment_constants import (
    CONTACTOR_NAMES,
    PKD_NAME,
    FIRE_SYSTEM_NAME,
    GEARBOX_COVER_NAME,
    AMORTIZER_NAMES,
    RELAY_NAMES,
    NAME_ALIASES,
    DESIGNATION_ALIASES,
    NAME_CONTAINS_ALIASES,
    CODE_RULES,
    _key,
)
from myapp.models.product_passports import ProductPassportNode

NumberedPassportLinks = dict[tuple[int, str], tuple[int, int | None] | None]


class ProductPassportEquipmentService:
    """Связывает проверенные позиции паспортов с классификатором"""

    @staticmethod
    def match_key(
        tree_name: str | None,
        designation: str | None,
        supplier: str | None,
        manufacturer: str | None,
    ) -> str:
        """Считает ключ точного соответствия по исходным полям Omega"""
        values = [
            " ".join((value or "").casefold().replace("ё", "е").split())
            for value in (tree_name, designation, supplier, manufacturer)
        ]
        payload = json.dumps(values, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def remember_numbered_link(
        cls,
        links: NumberedPassportLinks,
        locomotive_model_id: int,
        node: ProductPassportNode,
    ) -> None:
        """Сохраняет однозначную связь номерного узла для такой же безномерной позиции"""
        if not (node.serial_number or "").strip() or node.equipment_id is None:
            return
        key = (
            locomotive_model_id,
            cls.match_key(
                node.tree_name,
                node.designation,
                node.omega_supplier_raw,
                node.manufacturer,
            ),
        )
        candidate = (node.equipment_id, node.supplier_id)
        if key in links and links[key] != candidate:
            links[key] = None
        else:
            links[key] = candidate

    @classmethod
    def inherit_numbered_links(
        cls,
        locomotive_model_id: int,
        nodes: list[ProductPassportNode],
        saved_links: NumberedPassportLinks | None = None,
    ) -> None:
        """Привязывает безномерные узлы только при единственном совпадении с номерными"""
        links = dict(saved_links or {})
        for node in nodes:
            cls.remember_numbered_link(links, locomotive_model_id, node)

        for node in nodes:
            if (node.serial_number or "").strip():
                continue
            key = (
                locomotive_model_id,
                cls.match_key(
                    node.tree_name,
                    node.designation,
                    node.omega_supplier_raw,
                    node.manufacturer,
                ),
            )
            match = links.get(key)
            if match is None:
                continue
            equipment_id, supplier_id = match
            if node.equipment_id not in (None, equipment_id):
                continue
            if supplier_id is not None and node.supplier_id not in (None, supplier_id):
                continue
            node.equipment_id = equipment_id
            if supplier_id is not None:
                node.supplier_id = supplier_id

    @staticmethod
    def _matches(value: str, pattern: str, mode: str) -> bool:
        if mode == "exact":
            return value == pattern
        if mode == "prefix":
            return value.startswith(pattern)
        if mode == "regex":
            return re.fullmatch(pattern, value) is not None
        return pattern in value

    @classmethod
    def _resolve_primary(cls, name: str, code: str) -> str | None:
        # В противоречивых строках Omega название контактора подтверждается соседними позициями
        contactor = re.search(r"АМ-3[,.]0-(400|800)-(01|02)(?!\d)", name)
        if contactor and "КОНТАКТОР" in name:
            return CONTACTOR_NAMES[contactor.groups()]
        if "ПЕРЕКЛЮЧАТЕЛЬ КУЛАЧКОВЫЙ" in name and re.search(
            r"ПКД-142(?:-02)?(?!\d)", name
        ):
            return PKD_NAME
        if "СИСТЕМА ПОЖАРНОЙ СИГНАЛИЗАЦИИ" in name and re.search(
            r"СПСТ\s+ЭЛ4-0?4-2ЭС6(?:\.С)?(?!\w)", name
        ):
            return FIRE_SYSTEM_NAME
        if (
            "КОЖУХ РЕДУКТОРА" in name
            and ("ЛЕВЫЙ" in name or "ПРАВЫЙ" in name)
            and code in {"2ЭС6.31.130.000", "2ЭС6.31.130.000-01"}
        ):
            return GEARBOX_COVER_NAME
        return None

    @staticmethod
    def _resolve_special(name: str) -> str | None:
        if "ПНКВ-1-1А" in name and "-03" not in name:
            return "ПНКВ_1_1А"
        if re.search(r"РЕАКТОР\s+Р-1,5/1000\s*П\s*У2", name):
            return "Р_1.5\\1000_П_У2"
        valve = re.search(r"КЭО\s+15/10/050/113(?:/(10|7))?(?!\d)", name)
        if valve:
            suffix = f"\\{valve.group(1)}" if valve.group(1) else ""
            return "КЭО_15\\10\\050\\113" + suffix
        if "ЭДТ-810У1" in name and "ЭК-810Ч" not in name:
            if "ЯКОРЬ ЭЛЕКТРОДВИГАТЕЛЯ" in name:
                return "Якорь_ЭДТ810"
            if "ТЯГОВЫЙ ДВИГАТЕЛЬ" in name:
                return "ЭДТ-810"
        if "АВТОСЦЕПКА СА-3" in name and "СЕРВИС" not in name:
            return "СА_3"
        if "ПОВОДОК ТЭД" in name and re.search(r"КП[1-4]", name):
            return "Поводок_ТЭД"
        return None

    @staticmethod
    def _resolve_ek_motor(name: str, code: str) -> str | None:
        if "ЭДТ" in name:
            return None
        if "ТЯГОВЫЙ ДВИГАТЕЛЬ ЭК-810Ч" in name and code == "ДИЖЦ.652451.003":
            return "ЭК-810Ч"
        if "ЯКОРЬ ЭЛЕКТРОДВИГАТЕЛЯ ЭК-810Ч" in name and code.startswith(
            "ДИЖЦ.684263.019-02"
        ):
            return "Якорь_ЭК810"
        return None

    @classmethod
    def _resolve_relay(cls, name: str, supplier_name: str | None) -> str | None:
        if "РЕЛЕ ДИФФЕРЕНЦИАЛЬНОЙ ЗАЩИТЫ" not in name:
            return None
        variant = re.search(r"РДЗ-068(?:-(01|02))?(?!\d)", name)
        if not variant:
            return None
        supplier = (supplier_name or "").upper()
        for manufacturer in ("ЛЭМЗ", "КЗТМ"):
            if manufacturer in supplier:
                return RELAY_NAMES[(manufacturer, variant.group(1) or "")]
        return None

    @classmethod
    def _fallback_target(
        cls,
        locomotive_model_id: int,
        tree_name: str,
        designation: str | None,
        serial_number: str | None = None,
        supplier_name: str | None = None,
        manufacturer: str | None = None,
    ) -> str | None:
        """Возвращает внутренний ключ записи для поиска ID в классификаторе"""
        if locomotive_model_id not in (1, 6):
            return None

        name = tree_name.upper().replace("–", "-").replace("—", "-")
        code = (designation or "").upper().replace("–", "-").replace("—", "-")
        if name.startswith("ОГРАНИЧИТЕЛЬ ПЕРЕНАПРЯЖЕНИЙ"):
            maker = (manufacturer or "").upper()
            if "ЭКИ" in maker:
                return "ОПН_3.3_ЭМ_УХЛ1"
            if "ЗАИ" in maker:
                return "ОПН_3,3_ЭМ_УХЛ1(ЗАИ)"
            return None
        if name.startswith("УЗЕЛ КОМПАКТНЫЙ КОНИЧЕСКИЙ БУКСОВОГО ПОДШИПНИКА"):
            if code.replace(" ", "") == "3506/177.787-2LS":
                return "3506/177.787_2LS"
            return None
        primary = cls._resolve_primary(name, code)
        if primary:
            return primary

        if "АМОРТИЗАТОР" in name and re.search(r"5BV002[PР]", code):
            return "26Т.018"
        if "АМОРТИЗАТОР" in name and code == "26Т.081.02.000":
            serial = (serial_number or "").strip()
            if serial.isdecimal():
                if len(serial) == 7:
                    return "26Т.018"
                if len(serial) == 5:
                    return AMORTIZER_NAMES["five"]
                if len(serial) < 5:
                    return AMORTIZER_NAMES["short"]
            return None
        if (
            not code
            and name in {"АМОРТИЗАТОР ЛЕВЫЙ, КП4", "АМОРТИЗАТОР ПРАВЫЙ, КП3"}
            and (serial_number or "").strip().isdecimal()
            and len((serial_number or "").strip()) == 5
        ):
            return AMORTIZER_NAMES["five"]

        if not (code or (serial_number or "").strip()):
            return None

        special = (
            cls._resolve_relay(name, supplier_name)
            or cls._resolve_special(name)
            or cls._resolve_ek_motor(name, code)
        )
        if special:
            return special
        for name_pattern, name_mode, code_pattern, code_mode, target in CODE_RULES:
            if cls._matches(name, name_pattern, name_mode) and cls._matches(
                code, code_pattern, code_mode
            ):
                return target
        for fragment, target in NAME_CONTAINS_ALIASES:
            if fragment in name:
                return target
        return NAME_ALIASES.get(_key(tree_name)) or DESIGNATION_ALIASES.get(
            _key(designation)
        )

    @classmethod
    def resolve_match(
        cls,
        node: ProductPassportNode,
        equipment_match_ids: dict[str, tuple[int, int | None]] | None = None,
        equipment_serial_match_ids: (
            dict[tuple[str, int], tuple[int, int | None]] | None
        ) = None,
    ) -> tuple[int, int | None] | None:
        """Ищет подтверждённую связь с учётом заводского номера"""
        match_key = cls.match_key(
            node.tree_name,
            node.designation,
            node.omega_supplier_raw,
            node.manufacturer,
        )
        serial = (node.serial_number or "").strip()
        match = None
        if serial:
            match = (equipment_serial_match_ids or {}).get((match_key, len(serial)))
        if serial and match is None:
            match = (equipment_match_ids or {}).get(match_key)
        return match

    @classmethod
    def resolve_id(
        cls,
        locomotive_model_id: int,
        node: ProductPassportNode,
        equipment_index: dict[str, list[tuple[int, int | None]]],
        supplier_names: dict[int, str] | None = None,
        equipment_match_ids: dict[str, tuple[int, int | None]] | None = None,
        equipment_serial_match_ids: (
            dict[tuple[str, int], tuple[int, int | None]] | None
        ) = None,
        parent_equipment_id: int | None = None,
    ) -> int | None:
        """Возвращает ID оборудования, сохраняя исходные поля Omega"""
        if locomotive_model_id not in (1, 6, 3, 7):
            return None
        if locomotive_model_id in (3, 7) and (
            node.designation == "ДТ.520202.069"
            and "АЖ112М2FУХЛ1" in node.tree_name
            and parent_equipment_id is not None
        ):
            for target in ("АЖ112М2FУХЛ1", "АЖ112М2FУХЛ1_МЫС"):
                children = [
                    equipment_id
                    for equipment_id, parent_id in equipment_index.get(target, [])
                    if parent_id == parent_equipment_id
                ]
                if len(children) == 1:
                    return children[0]
        match = cls.resolve_match(node, equipment_match_ids, equipment_serial_match_ids)
        if match is not None:
            return match[0]
        name = cls._fallback_target(
            locomotive_model_id,
            node.tree_name,
            node.designation,
            node.serial_number,
            (supplier_names or {}).get(node.supplier_id) or node.omega_supplier_raw,
            node.manufacturer,
        )
        if not name:
            return None
        candidates = equipment_index.get(name, [])
        if parent_equipment_id is not None:
            children = [
                equipment_id
                for equipment_id, parent_id in candidates
                if parent_id == parent_equipment_id
            ]
            if len(children) == 1:
                return children[0]
            if len(children) > 1:
                return None
        return candidates[0][0] if candidates else None

    @staticmethod
    def redundant_parents(
        assignments: list[tuple[int, int, int | None, int | None]],
    ) -> set[tuple[int, int]]:
        """Находит групповые узлы с тем же оборудованием, что и у дочернего узла"""
        by_code = {
            (passport_id, omega_code): equipment_id
            for passport_id, omega_code, _, equipment_id in assignments
        }
        return {
            (passport_id, parent_omega_code)
            for passport_id, _, parent_omega_code, equipment_id in assignments
            if equipment_id is not None
            and parent_omega_code is not None
            and by_code.get((passport_id, parent_omega_code)) == equipment_id
        }
