/** Восстанавливает путь от корня до оборудования без зацикливания */
export function getEquipmentPath(id, equipmentMap) {
  const path = [];
  const visited = new Set();
  let item = equipmentMap.get(Number(id));
  while (item) {
    if (visited.has(item.id)) return [];
    visited.add(item.id);
    path.push(item);
    item = equipmentMap.get(item.parent_id);
  }
  return path.reverse();
}

/** Дополняет паспортный набор предками сохранённого выбора архивного случая */
export function passportAllowedIds(ids, selectedId, equipmentMap) {
  const allowed = new Set(ids);
  if (selectedId)
    getEquipmentPath(selectedId, equipmentMap).forEach((item) =>
      allowed.add(item.id),
    );
  return allowed;
}

/** Находит родительские экземпляры выбранных элементов без повторов */
export function passportParentInstances(selected, nodesByCode, equipmentId) {
  const parents = new Map();
  for (const selectedNode of selected) {
    let node = nodesByCode.get(selectedNode.parent_omega_code);
    const seen = new Set();
    while (node && !seen.has(node.id)) {
      seen.add(node.id);
      if (node.equipment_id === equipmentId) {
        parents.set(node.id, node);
        break;
      }
      node = nodesByCode.get(node.parent_omega_code);
    }
  }
  return [...parents.values()];
}

/** Ограничивает уровень ближайшим выбранным предком, а без предков показывает весь уровень */
export function filterEquipmentLevel(items, equipmentMap, levels, levelIndex) {
  let parentId = null;
  for (let i = levelIndex - 1; i >= 0; i--) {
    if (levels[`lvl${i}`]) {
      parentId = levels[`lvl${i}`];
      break;
    }
  }
  return items.filter(
    (item) =>
      item.calculatedLevel === levelIndex &&
      (!parentId ||
        getEquipmentPath(item.id, equipmentMap)
          .slice(0, -1)
          .some((parent) => parent.id === parentId)),
  );
}
