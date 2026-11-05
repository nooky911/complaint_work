import { useMemo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../../api/api";
import { formatToDB } from "../../utils/formatters";
import { trainCasePayload } from "../utils/caseFormData";
import { formatWagonNumbers } from "../../utils/formatters";
import { useEquipmentHierarchy } from "../../hooks/equipment/useEquipmentHierarchy";
import {
  text,
  resetTrainEquipment,
  trainEquipmentName,
  restoreTrainPassportParents,
} from "../utils/caseFormData";
import {
  passportAllowedIds,
  passportParentInstances,
} from "../../utils/equipmentHierarchy";

/** Адаптирует четыре поездных уровня и паспортные экземпляры к общей форме */
export function useTrainEquipment(
  { data, setData, update, editing, user },
  r,
  passport,
) {
  useEffect(() => {
    if (!data.id || !passport.data || passport.isFetching) return;
    setData((previous) =>
      restoreTrainPassportParents(previous, passport.data.nodes || []),
    );
  }, [
    data.id,
    data.train.component_id,
    data.train.element_id,
    data.train.passport_node_ids,
    passport.data,
    passport.isFetching,
    setData,
  ]);
  const eq = useMemo(() => r.equipment || [], [r.equipment]);
  const byId = useMemo(() => new Map(eq.map((x) => [x.id, x])), [eq]);
  const train = (key, value) =>
    setData((d) => ({
      ...d,
      replacement_items: [],
      _passport_replacement_invalid: true,
      train: { ...d.train, [key]: value ?? null },
    }));
  const handleTrainSelection = (selection) =>
    setData((d) => {
      const levels = selection.fullHierarchy;
      const sameComponent = levels.lvl3 && levels.lvl3 === d.train.component_id;
      const kept = sameComponent
        ? (passport.data?.nodes || []).filter(
            (node) =>
              node.equipment_id === levels.lvl3 &&
              d.train.passport_node_ids.includes(node.id),
          )
        : [];
      return {
        ...resetTrainEquipment(d),
        ...(kept.length
          ? {
              component_quantity: d.component_quantity,
              component_serial_number_old: d.component_serial_number_old,
              component_manufacture_date_old: d.component_manufacture_date_old,
            }
          : {}),
        train: {
          ...resetTrainEquipment(d).train,
          type_id: levels.lvl0,
          equipment_id: levels.lvl1,
          component_id: levels.lvl3,
          element_id: levels.lvl4,
          passport_node_ids: kept.map((node) => node.id),
        },
      };
    });
  const leaf =
    data.train.element_id || data.train.component_id || data.train.equipment_id;
  const supplier = (() => {
    let e = byId.get(leaf);
    const seen = new Set();
    while (e && !seen.has(e.id)) {
      if (e.supplier_id)
        return r.suppliers.find((s) => s.id === e.supplier_id)?.name;
      seen.add(e.id);
      e = byId.get(e.parent_id);
    }
    return "—";
  })();
  const availableNodes = useMemo(() => {
    const nodes = passport.data?.nodes || [],
      byCode = new Map(nodes.map((n) => [n.omega_code, n]));
    return nodes.filter((n) => {
      if (!n.equipment_id || (byId.get(n.equipment_id)?.level || 0) < 2)
        return false;
      let p = n;
      const seen = new Set();
      while (p && !seen.has(p.id)) {
        if (data.train.wagon_node_ids.includes(p.id)) return p.id !== n.id;
        seen.add(p.id);
        p = byCode.get(p.parent_omega_code);
      }
      return false;
    });
  }, [passport.data, data.train.wagon_node_ids, byId]);
  const allowedIds = useMemo(
    () =>
      passportAllowedIds(
        passport.data?.allowed_equipment_ids || [],
        data.id ? leaf : null,
        byId,
      ),
    [passport.data, data.id, leaf, byId],
  );
  const classifierLoading =
    !data.passport_id ||
    !data.train.wagon_node_ids.length ||
    !passport.data ||
    passport.isFetching ||
    passport.isError;
  const wagonNames = new Map(
    (passport.data?.wagons || []).map((wagon) => [wagon.id, wagon.name]),
  );
  const nodesByCode = new Map(
    (passport.data?.nodes || []).map((node) => [node.omega_code, node]),
  );
  const componentNodes = availableNodes.filter(
    (node) =>
      node.equipment_id ===
      (data.train.component_id || data.train.equipment_id),
  );
  const elementNodes = availableNodes.filter(
    (node) => node.equipment_id === data.train.element_id,
  );
  const selectedComponents = componentNodes.filter((node) =>
    data.train.passport_node_ids.includes(node.id),
  );
  const belongsToComponents = (node, components) =>
    passportParentInstances([node], nodesByCode, data.train.component_id).some(
      (parent) => components.some((component) => component.id === parent.id),
    );
  const selectableElements = elementNodes.filter(
    (node) =>
      !componentNodes.length || belongsToComponents(node, selectedComponents),
  );
  const managedRoles = [
    ...(componentNodes.length ? ["component"] : []),
    ...(elementNodes.length ? ["element"] : []),
  ];
  const roleNodes = { component: componentNodes, element: selectableElements };
  const matchingNodes = [...componentNodes, ...selectableElements];
  const selectedElements = selectableElements.filter((node) =>
    data.train.passport_node_ids.includes(node.id),
  );
  const selectionError = classifierLoading
    ? "Выберите паспорт и вагон и дождитесь загрузки состава"
    : (componentNodes.length && !selectedComponents.length) ||
        (elementNodes.length && !selectedElements.length)
      ? "Выберите неисправные экземпляры согласно паспорту: сначала компонент, затем его элементы"
      : data.train.passport_node_ids.some(
            (id) => !matchingNodes.some((node) => node.id === id),
          )
        ? "Выбранный элемент не принадлежит выбранному компоненту"
        : null;
  const setInstances = (ids, role = "component") =>
    setData((d) => {
      const selected = roleNodes[role].filter((node) => ids.includes(node.id));
      const keptElements =
        role === "component"
          ? elementNodes.filter(
              (node) =>
                d.train.passport_node_ids.includes(node.id) &&
                (!componentNodes.length || belongsToComponents(node, selected)),
            )
          : selected;
      const components = role === "component" ? selected : selectedComponents;
      const related = {};
      for (const [kind, items] of [
        ["component", components],
        ["element", keptElements],
      ]) {
        if (!managedRoles.includes(kind)) continue;
        related[`${kind}_quantity`] = items.length;
        related[`${kind}_serial_number_old`] =
          items.map((node) => node.serial_number || "б/н").join(", ") || null;
        related[`${kind}_manufacture_date_old`] =
          items.map((node) => node.manufacture_date || "—").join(", ") || null;
      }
      return {
        ...d,
        ...related,
        replacement_items: [],
        _passport_replacement_invalid: true,
        train: {
          ...d.train,
          passport_node_ids: [...components, ...keptElements].map(
            (node) => node.id,
          ),
        },
      };
    });
  const prettyEquipment = useMemo(
    () =>
      eq.map((e) => ({
        ...e,
        name: text(e.name),
        calculatedLevel: [0, 1, 3, 4][e.level - 1],
      })),
    [eq],
  );
  const hierarchy = useEquipmentHierarchy({
    currentId:
      data.train.element_id ||
      data.train.component_id ||
      data.train.equipment_id ||
      data.train.type_id,
    allEquipment: prettyEquipment,
    mode: "old",
    currentData: data,
    updateField: update,
    isEditing: editing,
  });
  const levels = {
    lvl3: data.train.component_id || data.train.equipment_id,
    lvl4: data.train.element_id,
  };
  const sourceKey = {
    1: "equipment_id",
    2: "component_id",
    3: "element_id",
  }[data.repair_type_id];
  const replacementKey = sourceKey ? `new_${sourceKey}` : null;
  const source = byId.get(data.train[sourceKey]);
  const replacementLinks = (passport.data?.nodes || [])
    .filter((node) => data.train.passport_node_ids.includes(node.id))
    .map((node) => ({
      node_id: node.id,
      version: node.version,
      role:
        node.equipment_id === data.train.element_id ? "element" : "component",
    }));
  const replacementParams = {
    train: trainCasePayload(data).train,
    repair_type_id: Number(data.repair_type_id),
    fault_date: formatToDB(data.fault_date) || null,
    case_id: data.id || null,
    passport_links: replacementLinks,
  };
  const replacementQuery = useQuery({
    queryKey: [
      "train-replacement-preview",
      data.passport_id,
      replacementParams,
    ],
    queryFn: async ({ signal }) =>
      (
        await api.post(
          `/train/passports/${data.passport_id}/replacement-preview`,
          replacementParams,
          { signal },
        )
      ).data,
    enabled:
      editing && !!replacementKey && !classifierLoading && !selectionError,
    retry: false,
    staleTime: 0,
  });

  const selectedType =
    byId.get(data.train.equipment_id)?.parent_id || data.train.type_id;
  const displayEquipment = trainEquipmentName(data.train, byId);
  const equipmentContexts = data.train.wagon_node_ids.map((id, index) => ({
    section: id,
    section_name: formatWagonNumbers([
      wagonNames.get(id) || data.train.wagon_names?.[index] || "—",
    ]),
  }));
  const selectedNodes = availableNodes.filter((node) =>
    data.train.passport_node_ids.includes(node.id),
  );
  // Старые случаи могли хранить только элемент: родитель нужен лишь для отображения
  const displayNodes = [
    ...new Map(
      [
        ...selectedNodes,
        ...passportParentInstances(
          selectedNodes.filter(
            (node) => byId.get(node.equipment_id)?.level === 4,
          ),
          nodesByCode,
          data.train.component_id,
        ),
      ].map((node) => [node.id, node]),
    ).values(),
  ];
  const passportLinks = displayNodes.map((node) => ({
    node_id: node.id,
    role: byId.get(node.equipment_id)?.level === 4 ? "element" : "component",
    context:
      equipmentContexts.find((context) => context.section === node.wagon_id) ||
      {},
    state: {
      equipment_name: text(byId.get(node.equipment_id)?.name || node.name),
      serial_number: node.serial_number,
      manufacture_date_text: node.manufacture_date,
    },
  }));
  const replacementItems = equipmentContexts.flatMap((context) => {
    const roles = [
      ["component", data.train.new_component_id || data.train.new_equipment_id],
      ["element", data.train.new_element_id],
    ];
    return roles
      .filter(([, id]) => id)
      .map(([role, id]) => ({
        node_id: `train-installed-${context.section}-${role}`,
        role,
        context,
        equipment_name: text(byId.get(id)?.name),
        serial_number: data[`${role}_serial_number_new`],
        manufacture_date_text: data[`${role}_manufacture_date_new`],
      }));
  });
  const viewData = {
    ...data,
    direction: "train",
    repair_type_id: data.repair_type_id === 8 ? null : data.repair_type_id,
    repair_type: data.repair_type_id === 8 ? null : data.repair_type,
    equipment_contexts: equipmentContexts,
    passport_links: passportLinks,
    replacement_items: data.replacement_items?.length
      ? data.replacement_items
      : replacementItems,
    creator_full_name: data.user?.full_name || user.full_name,
    date_recorded: data.date_recorded || new Date().toISOString(),
    component_equipment: { id: levels.lvl3, name: displayEquipment || "—" },
    element_equipment: data.train.element_id
      ? {
          id: data.train.element_id,
          name: text(byId.get(data.train.element_id)?.name),
        }
      : null,
    new_component_equipment_id:
      data.train.new_component_id || data.train.new_equipment_id,
    new_element_equipment_id: data.train.new_element_id,
  };
  const headerData = {
    ...data,
    supplier_id: r.suppliers.find((s) => s.name === supplier)?.id,
  };
  const changeRepairType = (value) =>
    setData((d) => {
      const sourceField = {
        1: "equipment_id",
        2: "component_id",
        3: "element_id",
      }[value];
      const key = sourceField ? `new_${sourceField}` : null;
      return {
        ...d,
        repair_type_id: value,
        replacement_items: [],
        _passport_replacement_invalid: true,
        repair_type: null,
        performed_by_id: null,
        equipment_owner_id: null,
        destination_id: null,
        component_serial_number_new: null,
        component_manufacture_date_new: null,
        element_serial_number_new: null,
        element_manufacture_date_new: null,
        new_component_quantity: key && key !== "new_element_id" ? 1 : null,
        new_element_quantity: key === "new_element_id" ? 1 : null,
        train: {
          ...d.train,
          new_equipment_id: null,
          new_component_id: null,
          new_element_id: null,
          ...(key ? { [key]: d.train[sourceField] || null } : {}),
        },
      };
    });

  return {
    eq,
    byId,
    train,
    handleTrainSelection,
    leaf,
    supplier,
    availableNodes,
    wagonNames,
    matchingNodes,
    roleNodes,
    allowedIds,
    classifierLoading,
    passportError: passport.isError,
    retryPassport: passport.refetch,
    managedRoles,
    selectionError,
    setInstances,
    prettyEquipment,
    hierarchy,
    levels,
    replacementKey,
    replacementQuery,
    replacementLinks,
    source,
    selectedType,
    viewData,
    headerData,
    changeRepairType,
  };
}
