import { useMemo, useState } from "react";
import {
  Box,
  ChevronDown,
  ChevronRight,
  CircleDot,
  Hash,
  Wrench,
  Download,
  LoaderCircle,
  Search,
  Plus,
  Minus,
} from "lucide-react";

import { PassportPositionHistory } from "./PassportPositionHistory";
import { MultiSelectField } from "../inputs/MultiSelectField";
import { formatDate, sortOptionsByName } from "../../utils/formatters";
import { exportProductPassport } from "../../api/productPassports";

const DETAIL_FIELDS = [
  ["full_name", "Полное наименование"],
  ["article", "Артикул"],
  ["designation", "Обозначение"],
  ["serial_number", "Заводской номер"],
  ["manufacture_date", "Дата изготовления"],
  ["commissioned_at", "Дата ввода в эксплуатацию"],
  ["install_date", "Дата установки"],
  ["manufacturer", "Изготовитель"],
  ["supplier", "Поставщик"],
];

const DATE_FIELDS = new Set([
  "manufacture_date",
  "commissioned_at",
  "install_date",
]);

function sectionOrder(node) {
  for (const name of [node.tree_name, node.full_name]) {
    const normalized = (name || "").trim().toUpperCase();
    if (normalized.includes("БУСТЕР")) return 2;
    const section = normalized.match(
      /^СЕКЦИЯ\s+[«"']?([АAБB])(?=$|[\s»"'.,:№-])/,
    );
    if (section) return ["А", "A"].includes(section[1]) ? 0 : 1;
  }
  return 3;
}

/** Собирает найденные ветки с детьми и цепочками родителей */
function matchingBranches(matches, nodesById, childrenByParent) {
  const ids = new Set();
  const pending = [...matches];
  while (pending.length) {
    const node = pending.pop();
    if (ids.has(node.id)) continue;
    ids.add(node.id);
    pending.push(...(childrenByParent.get(String(node.id)) || []));
  }
  for (const match of matches) {
    let node = nodesById.get(match.parent_id);
    while (node && !ids.has(node.id)) {
      ids.add(node.id);
      node = nodesById.get(node.parent_id);
    }
  }
  return ids;
}

export function PassportTree({ passport }) {
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [equipmentNames, setEquipmentNames] = useState([]);
  const [numberIds, setNumberIds] = useState([]);
  const [visibleNodeIds, setVisibleNodeIds] = useState(null);
  const downloadPassport = async () => {
    if (exporting) return;
    setExporting(true);
    setExportError("");
    try {
      await exportProductPassport(passport.id);
    } catch {
      setExportError("Не удалось скачать паспорт. Попробуйте ещё раз.");
    } finally {
      setExporting(false);
    }
  };
  const { root, childrenByParent, nodesById } = useMemo(() => {
    const children = new Map();
    let rootNode = null;

    passport.nodes.forEach((node) => {
      if (node.parent_id === null) rootNode = node;
      const parentKey = String(node.parent_id ?? "root");
      if (!children.has(parentKey)) children.set(parentKey, []);
      children.get(parentKey).push(node);
    });

    // Меняем только порядок секций под локомотивом, сохраняя их состав
    if (rootNode) {
      children
        .get(String(rootNode.id))
        ?.sort((left, right) => sectionOrder(left) - sectionOrder(right));
    }

    return {
      root: rootNode,
      childrenByParent: children,
      nodesById: new Map(passport.nodes.map((node) => [node.id, node])),
    };
  }, [passport.nodes]);

  const numberedEquipment = useMemo(
    () =>
      passport.nodes.filter(
        (node) =>
          node.id !== root?.id &&
          sectionOrder(node) === 3 &&
          String(node.serial_number ?? "").trim(),
      ),
    [passport.nodes, root],
  );
  const equipmentOptions = useMemo(
    () =>
      sortOptionsByName(
        [
          ...new Set(
            numberedEquipment.map((node) =>
              (node.tree_name || node.full_name || "Без наименования").trim(),
            ),
          ),
        ].map((name) => ({ id: name, name })),
      ),
    [numberedEquipment],
  );
  const matchingEquipment = numberedEquipment.filter(
    (node) =>
      !equipmentNames.length ||
      equipmentNames.includes(
        (node.tree_name || node.full_name || "Без наименования").trim(),
      ),
  );
  const numberOptions = sortOptionsByName(
    matchingEquipment.map((node) => {
      let section = node;
      while (section.parent_id != null && section.parent_id !== root?.id) {
        section = nodesById.get(section.parent_id);
        if (!section) break;
      }
      return {
        id: node.id,
        name: `${section && section.id !== root?.id ? `${section.tree_name || section.full_name} · ` : ""}№ ${node.serial_number} · ${node.tree_name || node.full_name}`,
      };
    }),
  );

  const [expanded, setExpanded] = useState(
    () => new Set(root ? [root.id] : []),
  );
  const [selectedNodeId, setSelectedNodeId] = useState(root?.id);
  const selectedNode =
    passport.nodes.find((node) => node.id === selectedNodeId) || root;
  const expandableNodes = passport.nodes.filter(
    (node) =>
      (!visibleNodeIds || visibleNodeIds.has(node.id)) &&
      (childrenByParent.get(String(node.id)) || []).some(
        (child) => !visibleNodeIds || visibleNodeIds.has(child.id),
      ),
  );
  const allExpanded =
    expandableNodes.length > 0 &&
    expandableNodes.every((node) => expanded.has(node.id));

  /** Раскрывает все ветки паспорта или сворачивает их */
  const toggleAllNodes = () => {
    setExpanded(
      allExpanded ? new Set() : new Set(passport.nodes.map((node) => node.id)),
    );
  };

  /** Убирает выбранные номера, которые не относятся к выбранному оборудованию */
  const changeEquipment = (names) => {
    setEquipmentNames(names);
    const availableIds = new Set(
      numberedEquipment
        .filter(
          (node) =>
            !names.length ||
            names.includes(
              (node.tree_name || node.full_name || "Без наименования").trim(),
            ),
        )
        .map((node) => node.id),
    );
    setNumberIds((current) => current.filter((id) => availableIds.has(id)));
  };

  /** Применяет поиск и раскрывает найденные ветки паспорта */
  const applySearch = () => {
    if (!equipmentNames.length && !numberIds.length) {
      setVisibleNodeIds(null);
      return;
    }
    const matches = matchingEquipment.filter(
      (node) => !numberIds.length || numberIds.includes(node.id),
    );
    const ids = matchingBranches(matches, nodesById, childrenByParent);
    setVisibleNodeIds(ids);
    setExpanded(new Set(ids));
    if (!ids.has(selectedNodeId)) setSelectedNodeId(matches[0]?.id ?? root?.id);
  };

  /** Возвращает полный состав паспорта и очищает условия поиска */
  const resetSearch = () => {
    setEquipmentNames([]);
    setNumberIds([]);
    setVisibleNodeIds(null);
  };

  const toggleNode = (nodeId) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };

  const renderNode = (node, depth = 0) => {
    const children = (childrenByParent.get(String(node.id)) || []).filter(
      (child) => !visibleNodeIds || visibleNodeIds.has(child.id),
    );
    const hasChildren = children.length > 0;
    const isExpanded = expanded.has(node.id);
    const isSelected = selectedNode?.id === node.id;

    return (
      <div key={node.id}>
        <div
          className={`flex cursor-pointer items-center gap-2 rounded-lg py-2 pr-3 transition-colors ${
            isSelected
              ? "bg-indigo-50 text-indigo-700"
              : "text-slate-700 hover:bg-slate-50"
          }`}
          style={{ paddingLeft: `${Math.min(depth, 12) * 18 + 8}px` }}
          onClick={() => setSelectedNodeId(node.id)}
        >
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              if (hasChildren) toggleNode(node.id);
            }}
            className="flex h-5 w-5 shrink-0 items-center justify-center"
            aria-label={isExpanded ? "Свернуть узел" : "Развернуть узел"}
          >
            {hasChildren ? (
              isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )
            ) : (
              <CircleDot className="h-2.5 w-2.5 text-slate-300" />
            )}
          </button>
          <Box className="h-4 w-4 shrink-0 text-slate-400" />
          <span className="min-w-0 flex-1 truncate text-xs font-bold">
            {node.tree_name}
            {node.has_history ? " *" : ""}
          </span>
          {node.serial_number && (
            <span className="shrink-0 rounded-md bg-white px-2 py-0.5 text-[10px] font-black text-black shadow-sm">
              № {node.serial_number}
            </span>
          )}
        </div>
        {hasChildren &&
          isExpanded &&
          children.map((child) => renderNode(child, depth + 1))}
      </div>
    );
  };

  return (
    <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.6fr)]">
      <section className="flex min-h-[420px] flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 px-5 py-4">
          <div className="flex items-center gap-3">
            <h2 className="text-base font-black text-slate-900">
              Состав паспорта
            </h2>
            <button
              type="button"
              onClick={toggleAllNodes}
              aria-label={
                allExpanded ? "Свернуть весь паспорт" : "Раскрыть весь паспорт"
              }
              title={
                allExpanded ? "Свернуть весь паспорт" : "Раскрыть весь паспорт"
              }
              aria-expanded={allExpanded}
              className={`flex h-[27px] w-[27px] shrink-0 items-center justify-center rounded-lg border shadow-sm transition-colors ${allExpanded ? "border-slate-200 bg-slate-100 text-slate-600 hover:bg-slate-200" : "border-indigo-200 bg-indigo-50 text-indigo-600 hover:bg-indigo-100"}`}
            >
              {allExpanded ? (
                <Minus className="h-[17px] w-[17px]" />
              ) : (
                <Plus className="h-[17px] w-[17px]" />
              )}
            </button>
          </div>
          <div className="flex min-w-0 flex-1 flex-wrap items-end justify-end gap-3">
            {searchOpen ? (
              <>
                <div className="w-64 max-w-full">
                  <MultiSelectField
                    label="Оборудование"
                    placeholder="Выберите оборудование"
                    options={equipmentOptions}
                    selectedValues={equipmentNames}
                    onChange={changeEquipment}
                    allowClear
                  />
                </div>
                <div className="w-64 max-w-full">
                  <MultiSelectField
                    label="Заводские номера"
                    placeholder="Все номера"
                    options={numberOptions}
                    selectedValues={numberIds}
                    onChange={setNumberIds}
                    allowClear
                  />
                </div>
                <button
                  type="button"
                  onClick={applySearch}
                  className="h-[38px] rounded-lg bg-indigo-600 px-3 text-xs font-bold text-white hover:bg-indigo-700"
                >
                  Применить
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => setSearchOpen(true)}
                className="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-bold text-blue-700 hover:bg-blue-100"
              >
                <Search className="h-4 w-4" />
                Поиск
              </button>
            )}
            <div className="flex flex-wrap items-center justify-end gap-3">
              {searchOpen && (
                <>
                  <button
                    type="button"
                    onClick={resetSearch}
                    className="flex items-center rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-50"
                  >
                    Сбросить
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      resetSearch();
                      setSearchOpen(false);
                    }}
                    className="flex items-center rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-bold text-red-700 hover:bg-red-100"
                  >
                    Выйти из поиска
                  </button>
                </>
              )}
              <button
                type="button"
                onClick={downloadPassport}
                disabled={exporting}
                className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-3 py-1.5 text-xs font-bold text-green-700 transition-colors hover:bg-green-100 disabled:cursor-wait disabled:opacity-60"
              >
                {exporting ? (
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                {exporting ? "Создание файла…" : "Скачать Excel"}
              </button>
              <div className="rounded-lg bg-indigo-50 px-3 py-1.5 text-xs font-black text-indigo-600">
                {passport.locomotive_model_name} №{passport.product_number}
              </div>
            </div>
          </div>
        </div>
        {exportError && (
          <p role="alert" className="px-5 py-2 text-xs text-red-600">
            {exportError}
          </p>
        )}
        <div className="flex-1 overflow-auto p-2">
          {root &&
            (!visibleNodeIds || visibleNodeIds.has(root.id)) &&
            renderNode(root)}
          {visibleNodeIds?.size === 0 && (
            <p className="p-4 text-center text-sm text-slate-500">
              Оборудование не найдено
            </p>
          )}
        </div>
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm lg:sticky lg:top-4 lg:max-h-[calc(100vh-10rem)] lg:self-start lg:overflow-auto">
        {selectedNode ? (
          <>
            <div className="mb-5 border-b border-gray-100 pb-4">
              <div className="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                <Wrench className="h-5 w-5" />
              </div>
              <h2 className="text-base font-black text-slate-900">
                {selectedNode.tree_name}
              </h2>
            </div>
            <dl className="space-y-3">
              {DETAIL_FIELDS.map(([key, label]) => {
                const missingSupplier =
                  key === "supplier" &&
                  selectedNode.supplier_id == null &&
                  Boolean(
                    selectedNode.manufacturer || selectedNode.serial_number,
                  );
                const value = missingSupplier
                  ? "Поставщик пуст"
                  : key === "commissioned_at"
                    ? selectedNode.id === root?.id
                      ? passport.commissioned_at
                      : null
                    : selectedNode[key];
                if (value === null || value === undefined || value === "")
                  return null;
                const formattedValue = DATE_FIELDS.has(key)
                  ? formatDate(value)
                  : String(value);
                return (
                  <div key={key}>
                    <dt className="text-[10px] font-black tracking-wider text-slate-400 uppercase">
                      {label}
                    </dt>
                    <dd
                      className={`mt-0.5 text-sm font-semibold break-words ${missingSupplier ? "text-amber-700" : "text-slate-800"}`}
                    >
                      {formattedValue}
                    </dd>
                  </div>
                );
              })}
            </dl>
            <PassportPositionHistory
              key={`${selectedNode.id}-${selectedNode.version}`}
              passportId={passport.id}
              node={selectedNode}
            />
          </>
        ) : (
          <div className="flex h-full flex-col items-center justify-center text-slate-400">
            <Hash className="mb-3 h-8 w-8" />
            <span className="text-sm font-medium">Выберите узел дерева</span>
          </div>
        )}
      </section>
    </div>
  );
}
