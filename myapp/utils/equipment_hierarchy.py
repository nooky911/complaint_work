import re


def inherited_equipment_value(equipment_id, equipment, field):
    """Возвращает собственное значение либо ближайшее заполненное значение родителя"""
    seen = set()
    while equipment_id is not None and equipment_id not in seen:
        seen.add(equipment_id)
        item = equipment.get(equipment_id)
        if item is None:
            break
        value = (
            item.get(field) if isinstance(item, dict) else getattr(item, field, None)
        )
        if value is not None and value != "":
            return value
        equipment_id = (
            item.get("parent_id") if isinstance(item, dict) else item.parent_id
        )
    return None


def passport_classifier_ids(equipment, known_ids, present_ids, managed_level=None):
    """Оставляет паспортные позиции области и ветки для ручного ввода"""
    paths = {}
    for equipment_id in equipment:
        path, seen, current = [], set(), equipment_id
        while current in equipment and current not in seen:
            seen.add(current)
            path.append(current)
            item = equipment[current]
            current = (
                item.get("parent_id") if isinstance(item, dict) else item.parent_id
            )
        paths[equipment_id] = list(reversed(path))
    managed = set()
    for equipment_id in known_ids:
        path = paths.get(equipment_id, [])
        if managed_level is None and len(path) >= 2:
            managed.add(equipment_id)
        elif managed_level is not None and len(path) >= managed_level:
            managed.add(path[managed_level - 1])
    if managed_level is None:
        # Соседство само по себе не делает ручную позицию паспортным исполнением
        families = {}
        for key, path in paths.items():
            if not 2 <= len(path) <= 3:
                continue
            item = equipment[key]
            name = (
                item.get("equipment_name", item.get("name", ""))
                if isinstance(item, dict)
                else item.equipment_name
            )
            designation = (
                item.get("designation") if isinstance(item, dict) else item.designation
            )
            normalize = lambda value: re.sub(r"\W+|_", "", (value or "").casefold())
            name, designation = normalize(name), normalize(designation)
            if not designation or not name.endswith(designation):
                continue
            base = name[: -len(designation)]
            if base:
                families.setdefault((path[-2], base), set()).add(key)
        for variants in families.values():
            if variants & managed:
                managed.update(variants)
    available = {
        parent for equipment_id in present_ids for parent in paths.get(equipment_id, [])
    }
    allowed = {
        equipment_id
        for equipment_id, path in paths.items()
        if not any(parent in managed and parent not in available for parent in path)
    }
    children = {}
    for equipment_id, path in paths.items():
        if len(path) > 1:
            children.setdefault(path[-2], set()).add(equipment_id)
    for equipment_id in sorted(
        equipment, key=lambda item_id: len(paths[item_id]), reverse=True
    ):
        if children.get(equipment_id) and not children[equipment_id] & allowed:
            allowed.discard(equipment_id)
    return sorted(allowed)
