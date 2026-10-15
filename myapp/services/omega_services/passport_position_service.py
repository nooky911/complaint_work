import re
from collections import defaultdict
from datetime import datetime
from typing import Any
from sqlalchemy import select

from myapp.models.equipment_malfunctions import Equipment
from myapp.models.product_passports import (
    ProductPassportEvent,
    ProductPassportEventItem,
)
from myapp.services import CaseValidationError
from myapp.services.omega_services.product_passport_service import (
    ProductPassportService,
)


class PassportPositionService:
    """Выбор позиций паспорта и состава замены"""

    INSTANCE_FIELDS = (
        "equipment_id",
        "equipment_name",
        "serial_number",
        "manufacture_date_text",
        "manufacture_date",
        "supplier_id",
        "manufacturer",
        "install_date",
        "designation",
        "full_name",
        "tree_name",
    )

    REPLACEMENT_TYPES = {1, 2, 3}

    @staticmethod
    def fail(message, field="passport_links"):
        """Сообщает об ошибке выбора или изменения паспорта"""
        raise CaseValidationError(field, message)

    @staticmethod
    def clean(value):
        """Убирает пробелы и заменяет пустую строку на None"""
        return value.strip() or None if isinstance(value, str) else value

    @staticmethod
    def snapshot(node, equipment):
        """Сохраняет данные оборудования на выбранной позиции"""
        return dict(
            schema_version=1,
            is_present=node.is_present,
            equipment_id=node.equipment_id,
            equipment_name=equipment.get(node.equipment_id, {}).get("name"),
            serial_number=node.serial_number,
            manufacture_date_text=node.manufacture_date_text
            or (
                node.manufacture_date.strftime("%d.%m.%Y")
                if node.manufacture_date
                else None
            ),
            manufacture_date=(
                node.manufacture_date.isoformat() if node.manufacture_date else None
            ),
            supplier_id=node.supplier_id,
            manufacturer=node.manufacturer,
            install_date=node.install_date.isoformat() if node.install_date else None,
            designation=node.designation,
            full_name=node.full_name,
            tree_name=node.tree_name,
        )

    @staticmethod
    def compose(baseline, changes):
        """Применяет изменения к исходным данным позиции"""
        state = dict(baseline)
        for item in changes:
            for field in item.changed_fields:
                state[field] = item.after_state.get(field)
        return state

    @staticmethod
    async def equipment(session):
        """Читает типы оборудования и их поставщиков"""
        rows = (
            await session.execute(
                select(
                    Equipment.id,
                    Equipment.equipment_name,
                    Equipment.parent_id,
                    Equipment.supplier_id,
                )
            )
        ).all()
        return {
            r.id: {
                "name": r.equipment_name,
                "parent_id": r.parent_id,
                "supplier_id": r.supplier_id,
            }
            for r in rows
        }

    @staticmethod
    def family(eid, equipment):
        """Возвращает родителя типа оборудования в классификаторе"""
        row = equipment.get(eid)
        return row.get("parent_id") if row else None

    @classmethod
    def allowed_types(cls, eid, equipment):
        """Возвращает допустимые типы для замены оборудования"""
        row = equipment.get(eid)
        if not row:
            return []
        family = cls.family(eid, equipment)
        return [
            {"id": key, "name": value["name"].replace("_", " ")}
            for key, value in equipment.items()
            if key == eid or (family is not None and value["parent_id"] == family)
        ]

    @classmethod
    async def load(cls, session, passport_id, as_of=None, exclude_case_id=None):
        """Читает состав паспорта на нужную дату"""
        passport = await ProductPassportService.get_by_id(session, passport_id)
        if passport is None:
            cls.fail("Паспорт не найден")
        equipment = await cls.equipment(session)
        nodes = {n.id: n for n in passport.nodes}
        changes = defaultdict(list)
        installations = {}
        stmt = (
            select(
                ProductPassportEventItem,
                ProductPassportEvent.kind,
                ProductPassportEvent.source_case_id,
            )
            .join(ProductPassportEvent)
            .where(
                ProductPassportEvent.passport_id == passport_id,
                ProductPassportEvent.status == "active",
            )
            .order_by(
                ProductPassportEvent.effective_date,
                ProductPassportEvent.day_order,
                ProductPassportEvent.id,
            )
        )
        if as_of:
            stmt = stmt.where(ProductPassportEvent.effective_date <= as_of)
        if exclude_case_id:
            stmt = stmt.where(
                (ProductPassportEvent.case_id != exclude_case_id)
                | ProductPassportEvent.case_id.is_(None)
            )
        for item, kind, source_case_id in (await session.execute(stmt)).all():
            changes[item.node_id].append(item)
            if kind == "case_replacement":
                installations[item.node_id] = source_case_id
        states = {
            n.id: cls.compose(
                n.baseline_state or cls.snapshot(n, equipment), changes[n.id]
            )
            for n in passport.nodes
        }
        for node_id, case_id in installations.items():
            states[node_id]["_installation_case_id"] = case_id
        by_code = {n.omega_code: n for n in passport.nodes}
        return passport, nodes, states, equipment, by_code

    @staticmethod
    def ancestors(node, by_code):
        """Перебирает позицию и её родителей до корня паспорта"""
        seen = set()
        while node and node.id not in seen:
            seen.add(node.id)
            yield node
            node = by_code.get(node.parent_omega_code)

    @classmethod
    def context(cls, node, by_code):
        """Определяет секцию, тележку, КП и сторону позиции"""
        chain = list(cls.ancestors(node, by_code))
        section = next(
            (
                ProductPassportService.section_bit(n.tree_name, n.full_name)
                for n in chain
                if ProductPassportService.section_bit(n.tree_name, n.full_name)
            ),
            0,
        )
        bogie = next(
            (n for n in chain if re.match(r"^тележка\s*\d", n.tree_name, re.I)), None
        )
        kp = None
        for n in chain:
            name = n.tree_name or ""
            # КП01 в названии предохранительного клапана не является номером колёсной пары
            match = re.search(
                r"(?<!\w)КП\s*([1-4])(?!\d)|(?<!\d)([1-4])\s*КП\b|кол[её]сная\s+пара\s*([1-4])(?!\d)",
                name,
                re.I,
            )
            if match:
                kp = int(next(v for v in match.groups() if v))
                break
        name = node.tree_name or ""
        side = (
            "левый"
            if re.search(r"\bлев", name, re.I)
            else "правый" if re.search(r"\bправ", name, re.I) else None
        )
        contactor = re.match(r"^\s*([КK]\d+[А-ЯA-Z]?)\b", name, re.I)
        position = contactor[1] if contactor and "контактор" in name.lower() else None
        caption = (
            ", ".join(x for x in [side, f"КП{kp}" if kp else None] if x)
            or position
            or "Позиция"
        )
        return {
            "section": section,
            "section_name": {1: "А", 2: "Б", 4: "Бустер"}.get(section, "Общее"),
            "bogie_id": bogie.id if bogie else None,
            "kp": kp,
            "side": side,
            "position": position,
            "caption": caption,
            "path": " / ".join(n.tree_name for n in reversed(chain)),
        }

    @classmethod
    def label(cls, node, state, by_code):
        """Составляет подпись позиции с заводским номером"""
        context = cls.context(node, by_code)
        prefix = context["caption"]
        if prefix == "Позиция":
            prefix = ""
        return (
            (prefix + " " if prefix else "")
            + "№ "
            + (state.get("serial_number") or "—")
        )

    @classmethod
    def candidates(cls, nodes, states, by_code, equipment_id, parent_nodes=None):
        """Находит экземпляры нужного типа под выбранным компонентом"""
        return [
            n
            for n in nodes.values()
            if equipment_id
            and states[n.id].get("equipment_id") == equipment_id
            and states[n.id].get("is_present", True)
            and (
                not parent_nodes
                or any(a.id in parent_nodes for a in cls.ancestors(n, by_code))
            )
        ]

    @classmethod
    async def options(
        cls,
        session,
        passport_id,
        component_id,
        element_id,
        section_mask,
        as_of,
        case_id=None,
        component_nodes=None,
    ):
        """Возвращает доступные экземпляры для выбора в случае"""
        _, nodes, states, _, by_code = await cls.load(
            session, passport_id, as_of, case_id
        )
        result = {"component": [], "element": [], "required_roles": []}
        for role, eid in [("component", component_id), ("element", element_id)]:
            if not eid:
                continue
            matches = cls.candidates(
                nodes,
                states,
                by_code,
                eid,
                component_nodes if role == "element" else None,
            )
            if matches:
                result["required_roles"].append(role)
            for n in matches:
                ctx = cls.context(n, by_code)
                if ctx["section"] and not (ctx["section"] & section_mask):
                    continue
                result[role].append(
                    {
                        "id": n.id,
                        "name": cls.label(n, states[n.id], by_code),
                        "version": n.version,
                        "state": states[n.id],
                        "context": ctx,
                        "ancestor_ids": [a.id for a in cls.ancestors(n, by_code)],
                    }
                )
            result[role].sort(
                key=lambda x: (x["context"]["section"], x["context"]["path"], x["id"])
            )
        return result

    @classmethod
    def is_kmb_failure(cls, eid, equipment):
        """Проверяет, относится ли неисправное оборудование к смене КМБ"""
        names, seen = [], set()
        while eid in equipment and eid not in seen:
            seen.add(eid)
            row = equipment[eid]
            names.append(row["name"].lower().replace("_", " "))
            eid = row["parent_id"]
        return any(
            "тэд" == n or "подшипник" in n or "тяговый двигатель" in n for n in names
        )

    @staticmethod
    def kmb_member(name):
        """Проверяет, входит ли позиция в заменяемый состав КМБ"""
        name = name.lower().replace("_", " ")
        return any(
            re.search(pattern, name)
            for pattern in (
                r"кол[её]сная пара",
                r"узел компактный.*подшипник",
                r"буксов.*подшипник",
                r"подшипник.*буксов",
                r"моторно.?осев.*подшипник",
                r"поводок тэд",
                r"тяговый (?:электро)?двигатель",
                r"(?:электро)?двигатель тяговый",
                r"корпус букс",
                r"кожух редуктора",
            )
        )

    @classmethod
    def descendants(cls, root, nodes, by_code):
        """Возвращает позицию вместе с её детьми"""
        return [
            n
            for n in nodes.values()
            if any(a.id == root.id for a in cls.ancestors(n, by_code))
        ]

    @classmethod
    def plan(cls, nodes, states, equipment, by_code, links, repair_type):
        """Составляет список позиций для заполнения установленного оборудования"""
        roots = {}
        if repair_type not in cls.REPLACEMENT_TYPES:
            return []
        chosen = [
            nodes[x["node_id"]]
            for x in links
            if x["role"] == ("element" if repair_type == 3 else "component")
        ]
        if repair_type == 1:
            failed = [nodes[x["node_id"]] for x in links]
            kmb = [
                n
                for n in failed
                if cls.is_kmb_failure(states[n.id].get("equipment_id"), equipment)
            ]
            if kmb:
                for failed_node in kmb:
                    ctx = cls.context(failed_node, by_code)
                    if not all([ctx["section"], ctx["bogie_id"], ctx["kp"]]):
                        cls.fail(
                            "Не удалось однозначно определить секцию, тележку и КП для смены КМБ. Уточните позицию в паспорте."
                        )
                    key = f"{ctx['section']}:{ctx['bogie_id']}:{ctx['kp']}"
                    members = [
                        n
                        for n in nodes.values()
                        if cls.kmb_member(n.tree_name)
                        and all(
                            cls.context(n, by_code)[k] == ctx[k]
                            for k in ("section", "bogie_id", "kp")
                        )
                    ]
                    # Включаем само оборудование, пропуская пустые промежуточные узлы
                    members = [
                        n
                        for n in members
                        if states[n.id].get("serial_number")
                        or states[n.id].get("equipment_id")
                        or not any(
                            v.parent_omega_code == n.omega_code for v in nodes.values()
                        )
                    ]
                    kp_roots = [
                        n
                        for n in members
                        if re.search(r"кол[её]сная пара", n.tree_name, re.I)
                    ]
                    ted_roots = [
                        n
                        for n in members
                        if re.search(
                            r"тяговый (?:электро)?двигатель|(?:электро)?двигатель тяговый",
                            n.tree_name,
                            re.I,
                        )
                    ]
                    if len(kp_roots) != 1 or len(ted_roots) != 1:
                        cls.fail(
                            "В составе КМБ должны однозначно определяться одна КП и один ТЭД. Исправьте состав паспорта."
                        )
                    for root in members:
                        roots[root.id] = (
                            "kmb",
                            key,
                            root.id in {kp_roots[0].id, ted_roots[0].id},
                        )
                chosen = []
        for root in chosen:
            roots[root.id] = (
                "element" if repair_type == 3 else "component",
                str(root.id),
                False,
            )
        planned = {}
        for rid, (scope, key, mandatory) in roots.items():
            root = nodes[rid]
            for n in cls.descendants(root, nodes, by_code):
                state = states[n.id]
                if not state.get("is_present", True):
                    continue
                if n.id != rid and not (
                    state.get("serial_number") or state.get("equipment_id")
                ):
                    continue
                if n.id in planned:
                    planned[n.id]["required_serial"] |= mandatory and n.id == rid
                    continue
                ctx = cls.context(n, by_code)
                planned[n.id] = {
                    "node_id": n.id,
                    "version": n.version,
                    "scope": scope,
                    "group_key": key,
                    "parent_node_id": (
                        by_code[n.parent_omega_code].id
                        if n.parent_omega_code in by_code
                        else None
                    ),
                    "context": ctx,
                    "label": n.tree_name,
                    "position": ctx["caption"],
                    "before_state": state,
                    "equipment_id": state.get("equipment_id"),
                    "serial_number": None,
                    "manufacture_date_text": None,
                    "required_serial": mandatory and n.id == rid,
                    "allowed_types": (
                        []
                        if scope == "kmb"
                        else cls.allowed_types(state.get("equipment_id"), equipment)
                    ),
                }
        children = defaultdict(list)
        for row in planned.values():
            row["parent_node_id"] = next(
                (
                    a.id
                    for a in cls.ancestors(nodes[row["node_id"]], by_code)
                    if a.id != row["node_id"] and a.id in planned
                ),
                None,
            )
            children[row["parent_node_id"]].append(row)

        def order(row):
            """Определяет порядок позиций внутри состава замены"""
            label = row["label"].lower()
            priority = (
                0
                if re.search(r"кол[её]сная пара", label)
                else (
                    1
                    if re.search(
                        r"тяговый (?:электро)?двигатель|(?:электро)?двигатель тяговый",
                        label,
                    )
                    else 2
                )
            )
            return row["context"]["section"], row["group_key"], priority, row["node_id"]

        ordered = []

        def visit(row, depth):
            """Добавляет позицию и её детей в список с глубиной вложенности"""
            row["depth"] = depth
            ordered.append(row)
            for child in sorted(children[row["node_id"]], key=order):
                visit(child, depth + 1)

        for root in sorted(children[None], key=order):
            visit(root, 0)
        return ordered

    @classmethod
    def validate_links(
        cls, nodes, states, by_code, links, component_id, element_id, section_mask
    ):
        """Проверяет тип, секцию и родителя выбранных экземпляров"""
        seen = set()
        for link in links:
            nid, role = link["node_id"], link["role"]
            if (
                nid not in nodes
                or role not in ("component", "element")
                or (nid, role) in seen
            ):
                cls.fail("Недопустимая или повторная позиция паспорта")
            seen.add((nid, role))
            n = nodes[nid]
            state = states[nid]
            expected = component_id if role == "component" else element_id
            if (
                state.get("equipment_id") != expected
                or not expected
                or not state.get("is_present", True)
            ):
                cls.fail(
                    "Тип выбранной позиции не соответствует неисправному оборудованию"
                )
            ctx = cls.context(n, by_code)
            if ctx["section"] and not section_mask & ctx["section"]:
                cls.fail("Выбрана позиция другой секции")
            parent_id = link.get("parent_node_id")
            if (
                role == "element"
                and any(x["role"] == "component" for x in links)
                and parent_id is None
            ):
                cls.fail("Для элемента должен быть выбран соответствующий компонент")
            if parent_id is not None:
                if not any(
                    x["node_id"] == parent_id and x["role"] == "component"
                    for x in links
                ):
                    cls.fail("Не выбран родительский компонент элемента")
                if not any(a.id == parent_id for a in cls.ancestors(n, by_code)):
                    cls.fail("Элемент не принадлежит выбранному компоненту")
        # Если у выбранного компонента нет такого ребёнка в паспорте, оставляем ручной ввод
        parent_nodes = {x["node_id"] for x in links if x["role"] == "component"}
        for role, eid in [("component", component_id), ("element", element_id)]:
            matches = cls.candidates(
                nodes, states, by_code, eid, parent_nodes if role == "element" else None
            )
            if matches and not any(x["role"] == role for x in links):
                cls.fail("Выберите паспортные экземпляры: " + role)

    @classmethod
    async def preview(cls, session, passport_id, data):
        """Проверяет выбор и показывает состав будущей замены"""
        _, nodes, states, equipment, by_code = await cls.load(
            session, passport_id, data["fault_date"], data.get("case_id")
        )
        cls.validate_links(
            nodes,
            states,
            by_code,
            data.get("passport_links", []),
            data["component_equipment_id"],
            data.get("element_equipment_id"),
            data["section_mask"],
        )
        return cls.plan(
            nodes,
            states,
            equipment,
            by_code,
            data["passport_links"],
            data["repair_type_id"],
        )

    @classmethod
    def replacement_state(cls, item, value, equipment, has_children=False):
        """Проверяет и собирает данные установленного оборудования"""
        old = item["before_state"]
        new: dict[str, Any] = dict(old)
        new.pop("_installation_case_id", None)
        eid = value.get("equipment_id", old.get("equipment_id"))
        allowed = {v["id"] for v in item["allowed_types"]}
        if item["scope"] == "kmb" and eid != old.get("equipment_id"):
            cls.fail("Типы внутри КМБ менять нельзя")
        if (
            item["scope"] != "kmb"
            and eid != old.get("equipment_id")
            and eid not in allowed
        ):
            cls.fail("Новый тип относится к другому семейству")
        if eid != old.get("equipment_id") and has_children:
            cls.fail(
                "У смены типа есть дети. Сначала уточните соответствие состава нового типа в паспорте."
            )
        serial = cls.clean(value.get("serial_number"))
        manufacture = cls.clean(value.get("manufacture_date_text"))
        if item["required_serial"] and (
            not serial or serial.casefold() in ("б/н", "-", "—")
        ):
            cls.fail("При смене КМБ обязательны номера КП и ТЭД")
        if manufacture and any(c.isalpha() for c in manufacture):
            cls.fail("Дата изготовления не должна содержать буквы")
        full_date = None
        if manufacture:
            for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
                try:
                    full_date = datetime.strptime(manufacture, fmt).date().isoformat()
                    break
                except ValueError:
                    pass
        eq = equipment.get(eid, {})
        new.update(
            equipment_id=eid,
            equipment_name=eq.get("name"),
            serial_number=serial,
            manufacture_date_text=manufacture,
            manufacture_date=full_date,
            supplier_id=eq.get("supplier_id"),
            manufacturer=None,
            install_date=None,
        )
        if eid != old.get("equipment_id"):
            new["tree_name"] = re.sub(
                re.escape(old.get("equipment_name", "").replace("_", " ")),
                eq.get("name", "").replace("_", " "),
                old.get("tree_name") or "",
                flags=re.I,
            )
            if new["tree_name"] == old.get("tree_name"):
                new["tree_name"] = (
                    item["context"].get("caption") + " "
                    if item["context"].get("caption") != "Позиция"
                    else ""
                ) + eq.get("name", "").replace("_", " ")
            new["designation"] = None
            new["full_name"] = None
        return new
