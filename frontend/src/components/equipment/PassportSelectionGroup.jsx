/** Оформляет выбор паспортных экземпляров одинаково в обоих направлениях */
export function PassportSelectionGroup({ role, count, children }) {
  return (
    <div className="space-y-2 rounded-lg border border-indigo-200 bg-indigo-50/40 p-3">
      <div className="flex items-baseline justify-between gap-4">
        <p className="min-w-0 text-sm font-bold text-indigo-900">
          {role === "component"
            ? "Неисправные компоненты"
            : "Неисправные элементы"}{" "}
          согласно паспорту
        </p>
        <p className="flex shrink-0 items-baseline gap-2 text-sm font-bold text-indigo-900">
          Количество:
          <span className="rounded-md bg-indigo-100 px-2 text-base font-black text-indigo-700">
            {count}
          </span>
        </p>
      </div>
      {children}
    </div>
  );
}
