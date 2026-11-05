import { passportParentInstances } from "../../utils/equipmentHierarchy";
const sharedFields = [
  "user_id",
  "fault_date",
  "passport_id",
  "regional_center_id",
  "fault_discovered_at_id",
  "malfunction_id",
  "repair_type_id",
  "component_quantity",
  "element_quantity",
  "new_component_quantity",
  "new_element_quantity",
  "mileage",
  "notes",
  "component_serial_number_old",
  "component_manufacture_date_old",
  "element_serial_number_old",
  "element_manufacture_date_old",
  "component_serial_number_new",
  "component_manufacture_date_new",
  "element_serial_number_new",
  "element_manufacture_date_new",
  "performed_by_id",
  "equipment_owner_id",
  "destination_id",
];
export const blank = () => ({
  fault_date: null,
  component_quantity: 1,
  warranty_work: {},
  waybill_doc: {},
  train: { wagon_node_ids: [], passport_node_ids: [] },
});
export const message = (e) =>
  typeof e.response?.data?.detail === "string"
    ? e.response.data.detail
    : Array.isArray(e.response?.data?.detail)
      ? e.response.data.detail.map((x) => x.msg).join("; ")
      : "Не удалось выполнить действие";
export const text = (value) => (value || "").replaceAll("_", " ");

/** Формирует поездной запрос без локомотивных и служебных полей */
export function trainCasePayload(data) {
  const payload = Object.fromEntries(
    sharedFields.filter((k) => data[k] !== undefined).map((k) => [k, data[k]]),
  );
  payload.train = Object.fromEntries(
    [
      "train_model_id",
      "wagon_node_ids",
      "equipment_id",
      "component_id",
      "element_id",
      "new_equipment_id",
      "new_component_id",
      "new_element_id",
      "passport_node_ids",
    ]
      .filter((k) => data.train[k] !== undefined)
      .map((k) => [k, data.train[k]]),
  );
  for (const [quantity, selected] of [
    ["element_quantity", data.train.element_id],
    [
      "new_component_quantity",
      data.train.new_equipment_id || data.train.new_component_id,
    ],
    ["new_element_quantity", data.train.new_element_id],
  ]) {
    if (!selected) payload[quantity] = null;
  }
  payload.expected_revision = data.revision;
  if (data.passport_links !== undefined)
    payload.passport_links = data.passport_links;
  if (data.replacement_items !== undefined)
    payload.replacement_items = [1, 2, 3].includes(
      Number(data.repair_type_id),
    )
      ? data.replacement_items.map(
          ({
            node_id,
            version,
            equipment_id,
            serial_number,
            manufacture_date_text,
          }) => ({
            node_id,
            version,
            equipment_id,
            serial_number,
            manufacture_date_text,
          }),
        )
      : [];
  payload.warranty_work = Object.fromEntries(
    Object.entries(data.warranty_work || {}).filter(
      ([k]) =>
        k.endsWith("_id") || k.endsWith("_number") || k.endsWith("_date"),
    ),
  );
  delete payload.warranty_work.case_id;
  payload.waybill_doc = Object.fromEntries(
    Object.entries(data.waybill_doc || {}).filter(
      ([k]) => k.startsWith("ttn_") || k.endsWith("_provider_id"),
    ),
  );

  return payload;
}

/** Очищает экземпляры и ремонт при смене паспортной области или неисправного оборудования */
export function resetTrainEquipment(data) {
  return {
    ...data,
    replacement_items: [],
    _passport_replacement_invalid: true,
    malfunction_id: null,
    repair_type_id: null,
    repair_type: null,
    performed_by_id: null,
    equipment_owner_id: null,
    destination_id: null,
    component_quantity: 1,
    element_quantity: null,
    component_serial_number_old: null,
    component_manufacture_date_old: null,
    element_serial_number_old: null,
    element_manufacture_date_old: null,
    new_component_quantity: null,
    new_element_quantity: null,
    component_serial_number_new: null,
    component_manufacture_date_new: null,
    element_serial_number_new: null,
    element_manufacture_date_new: null,
    train: {
      ...data.train,
      type_id: null,
      equipment_id: null,
      component_id: null,
      element_id: null,
      passport_node_ids: [],
      new_equipment_id: null,
      new_component_id: null,
      new_element_id: null,
    },
  };
}

/** Добавляет родительское имя только к компоненту, названному одним обозначением */
export function trainEquipmentName(train, equipment) {
  const component = equipment.get(train.component_id);
  const parent = equipment.get(train.equipment_id);
  if (!component) return text(parent?.name) || "—";
  const name = text(component.name);
  const designation = text(component.designation);
  return designation && name === designation && parent
    ? `${text(parent.name)} ${name}`
    : name;
}

/** Восстанавливает родительские ID старой записи, не очищая оборудование и номера */
export function restoreTrainPassportParents(data, nodes) {
  if (!data.id || !data.train.element_id || !data.train.component_id)
    return data;
  const selected = nodes.filter(
    (node) =>
      node.equipment_id === data.train.element_id &&
      data.train.passport_node_ids.includes(node.id),
  );
  const parents = passportParentInstances(
    selected,
    new Map(nodes.map((node) => [node.omega_code, node])),
    data.train.component_id,
  );
  const missing = parents.filter(
    (node) => !data.train.passport_node_ids.includes(node.id),
  );
  if (!missing.length) return data;
  return {
    ...data,
    train: {
      ...data.train,
      passport_node_ids: [
        ...missing.map((node) => node.id),
        ...data.train.passport_node_ids,
      ],
    },
  };
}
