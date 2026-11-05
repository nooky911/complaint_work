from sqlalchemy import select

from myapp.models.product_passports import ProductPassportNode
from myapp.services.omega_services.passport_position_service import (
    PassportPositionService,
)
from myapp.utils.equipment_hierarchy import passport_classifier_ids


async def passport_selection(
    session, passport_id, wagon_ids, fault_date=None, case_id=None
):
    """Читает состав на дату акта и ограничивает выбор связанными позициями вагонов"""
    passport, nodes, states, equipment, by_code = await PassportPositionService.load(
        session, passport_id, fault_date, case_id
    )
    if passport.train_model_id is None:
        PassportPositionService.fail("Выберите поездной паспорт")
    selected = set(wagon_ids)
    owners = {}
    for node in nodes.values():
        for parent in PassportPositionService.ancestors(node, by_code):
            if parent.id in selected:
                owners[node.id] = parent.id
                break
    known_ids = (
        await session.scalars(
            select(ProductPassportNode.train_equipment_id)
            .where(ProductPassportNode.train_equipment_id.is_not(None))
            .distinct()
        )
    ).all()
    present_ids = {
        states[node_id].get("equipment_id")
        for node_id in owners
        if states[node_id].get("is_present", True)
    }
    allowed = (
        passport_classifier_ids(equipment, known_ids, present_ids) if selected else []
    )
    return passport, nodes, states, equipment, owners, allowed


def train_passport_links(details, nodes, states, by_code, supplied=None):
    """Проверяет поездные экземпляры и связывает элементы с выбранными родителями"""
    selected = set(details.passport_node_ids)
    if len(selected) != len(details.passport_node_ids):
        PassportPositionService.fail("Позиции паспорта не должны повторяться")
    versions = {link['node_id']: link.get('version') for link in supplied or []}
    if supplied is not None and set(versions) != selected:
        PassportPositionService.fail("Обновите выбранные экземпляры паспорта")
    links = []
    for nid in sorted(selected):
        node = nodes.get(nid)
        if node is None:
            PassportPositionService.fail("Позиция отсутствует в паспорте")
        ancestors = PassportPositionService.ancestors(node, by_code)
        if not any(n.id in details.wagon_node_ids for n in ancestors):
            PassportPositionService.fail("Позиция не принадлежит выбранным вагонам")
        eid = states[nid].get('equipment_id')
        role = 'element' if details.element_id and eid == details.element_id else 'component'
        expected = details.element_id if role == 'element' else details.component_id or details.equipment_id
        if eid != expected or not states[nid].get('is_present', True):
            PassportPositionService.fail("Тип позиции не соответствует выбранному оборудованию")
        parent = next((n.id for n in ancestors if n.id != nid and n.id in selected
                       and states[n.id].get('equipment_id') == details.component_id), None)
        links.append(dict(node_id=nid, role=role, parent_node_id=parent if role == 'element' else None,
                          version=versions.get(nid)))
    return links


def train_replacement_plan(nodes, states, equipment, by_code, details, repair_type, links):
    """Рассчитывает поездную замену вместе с детьми через общий паспортный план"""
    if repair_type == 8:
        PassportPositionService.fail("Тип ремонта Другое недоступен для поездов")
    level = {1: 2, 2: 3, 3: 4}.get(repair_type)
    if level is None:
        return []
    field = {2: 'equipment_id', 3: 'component_id', 4: 'element_id'}.get(level)
    if field is None:
        PassportPositionService.fail("Не определён уровень поездной замены")
    source = getattr(details, field)
    installed = getattr(details, 'new_' + field)
    roots = {}
    for link in links:
        for node in PassportPositionService.ancestors(nodes[link['node_id']], by_code):
            if states[node.id].get('equipment_id') == source:
                roots[node.id] = dict(node_id=node.id, role='component')
                break
    plan = PassportPositionService.plan(nodes, states, equipment, by_code, list(roots.values()), 2)
    for row in plan:
        row['context'] = train_position_context(nodes[row['node_id']], by_code, details)
        row['scope'] = 'element' if level == 4 else 'component'
        row['role'] = 'element' if equipment.get(row['equipment_id'], {}).get('level') == 4 else 'component'
        if row['node_id'] in roots and installed:
            if installed not in {value['id'] for value in row['allowed_types']}:
                PassportPositionService.fail("Замена относится к другому семейству оборудования")
            row['equipment_id'] = installed
            row['allowed_types'] = [dict(id=installed, name=equipment[installed]['name'].replace('_', ' '))]
    return plan


def train_position_context(node, by_code, details):
    """Добавляет вагон к общему контексту паспортной позиции"""
    context = PassportPositionService.context(node, by_code)
    wagon = next((parent for parent in PassportPositionService.ancestors(node, by_code)
                  if parent.id in details.wagon_node_ids), None)
    if wagon is not None:
        context.update(section=wagon.id, section_name=wagon.tree_name, wagon_id=wagon.id)
    return context
