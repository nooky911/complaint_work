import { useMemo, useState } from "react";
import {
  Box,
  ChevronDown,
  ChevronRight,
  CircleDot,
  Hash,
  Wrench,
} from "lucide-react";

import { formatDate } from "../../utils/formatters";

const DETAIL_FIELDS = [
  ["full_name", "Полное наименование"],
  ["peshka", "Пэшка"],
  ["designation", "Обозначение"],
  ["serial_number", "Заводской номер"],
  ["manufacture_date", "Дата изготовления"],
  ["install_date", "Дата установки"],
  ["manufacturer", "Изготовитель"],
  ["supplier", "Поставщик"],
];

const DATE_FIELDS = new Set(["manufacture_date", "install_date"]);

export function PassportTree({ passport }) {
  const { root, childrenByParent } = useMemo(() => {
    const children = new Map();
    let rootNode = null;

    passport.nodes.forEach((node) => {
      if (node.parent_id === null) rootNode = node;
      const parentKey = String(node.parent_id ?? "root");
      if (!children.has(parentKey)) children.set(parentKey, []);
      children.get(parentKey).push(node);
    });

    return { root: rootNode, childrenByParent: children };
  }, [passport.nodes]);

  const [expanded, setExpanded] = useState(
    () => new Set(root ? [root.id] : []),
  );
  const [selectedNode, setSelectedNode] = useState(root);

  const toggleNode = (nodeId) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };

  const renderNode = (node, depth = 0) => {
    const children = childrenByParent.get(String(node.id)) || [];
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
          onClick={() => setSelectedNode(node)}
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
          </span>
          {node.serial_number && (
            <span className="shrink-0 rounded-md bg-white px-2 py-0.5 text-[10px] font-black text-slate-500 shadow-sm">
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
        <div className="flex items-center justify-between border-b border-gray-100 px-5 py-4">
          <h2 className="text-base font-black text-slate-900">
            Состав паспорта
          </h2>
          <div className="rounded-lg bg-indigo-50 px-3 py-1.5 text-xs font-black text-indigo-600">
            {passport.locomotive_model_name} №{passport.product_number}
          </div>
        </div>
        <div className="flex-1 overflow-auto p-2">
          {root && renderNode(root)}
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
                const value = selectedNode[key];
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
                    <dd className="mt-0.5 text-sm font-semibold break-words text-slate-800">
                      {formattedValue}
                    </dd>
                  </div>
                );
              })}
            </dl>
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
