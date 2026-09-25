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

class ProductPassportEquipmentService:
    """Связывает проверенные позиции паспортов 2ЭС6 и 3ЭС6 с классификатором"""

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
    def resolve_name(
        cls,
        locomotive_model_id: int,
        tree_name: str,
        designation: str | None,
        serial_number: str | None = None,
        supplier_name: str | None = None,
    ) -> str | None:
        """Определяет запись классификатора только для согласованных позиций"""
        if locomotive_model_id not in (1, 6):
            return None

        name = tree_name.upper().replace("–", "-").replace("—", "-")
        code = (designation or "").upper().replace("–", "-").replace("—", "-")
        primary = cls._resolve_primary(name, code)
        if primary:
            return primary

        if "АМОРТИЗАТОР" in name and re.search(r"5BV002[PР]", code):
            return "26Т.018"
        if "АМОРТИЗАТОР" in name and code == "26Т.081.02.000":
            serial = (serial_number or "").strip()
            if serial.isdecimal():
                if len(serial) == 5:
                    return AMORTIZER_NAMES["five"]
                if len(serial) < 5:
                    return AMORTIZER_NAMES["short"]
            return None

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
    def resolve_id(
        cls,
        locomotive_model_id: int,
        node: ProductPassportNode,
        equipment_ids: dict[str, int],
        supplier_names: dict[int, str] | None = None,
    ) -> int | None:
        """Возвращает ID оборудования, сохраняя исходные поля Omega"""
        name = cls.resolve_name(
            locomotive_model_id,
            node.tree_name,
            node.designation,
            node.serial_number,
            (supplier_names or {}).get(node.supplier_id) or node.omega_supplier_raw,
        )
        return equipment_ids.get(name) if name else None

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
