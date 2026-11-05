import { Filter, Plus, ArrowUpDown, X, Download } from "lucide-react";
import { SectionsMenu } from "../Layout/SectionsMenu";
import { CaseNumberSearch } from "./CaseNumberSearch";

/** Общая панель управления списком случаев обоих направлений */
export function DashboardToolbar({
  direction = "loco",
  activeCount = 0,
  onOpenFilters,
  handleClearAllFilters,
  sortOrder,
  onSort,
  quickCaseNumber,
  onCaseNumberChange,
  totalCount,
  restricted = false,
  isSuperadmin = false,
  handleExport,
  isExporting = false,
  canCreate,
  onCreate,
  createDisabled = false,
  filtersMock = false,
  exportMock = false,
}) {
  return (
    <div className="flex w-full flex-shrink-0 items-start justify-between px-4 pt-2 md:px-3">
      <div className="flex flex-col gap-2">
        {/* БЛОК КНОПОК */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Кнопка фильтров */}
          <button
            onClick={onOpenFilters}
            disabled={filtersMock}
            title={filtersMock ? "Пока недоступно" : undefined}
            className={`flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-black tracking-wider uppercase shadow-sm transition-all active:scale-95 ${
              activeCount > 0
                ? "border-indigo-600 bg-indigo-600 text-white shadow-indigo-200"
                : "border-indigo-100 bg-indigo-50 text-indigo-600 hover:border-indigo-200 hover:bg-indigo-100"
            }`}
          >
            <Filter
              className={`h-3 w-3 ${activeCount > 0 ? "fill-white" : "fill-indigo-500"}`}
            />
            Параметры поиска
            {activeCount > 0 && (
              <span className="ml-1 flex h-4 w-4 items-center justify-center rounded-full bg-white text-[9px] font-black text-indigo-600">
                {activeCount}
              </span>
            )}
          </button>

          {/* Кнопка очистки фильтров */}
          {activeCount > 0 && (
            <button
              onClick={handleClearAllFilters}
              className="flex items-center justify-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-[11px] font-black tracking-wider text-red-600 uppercase shadow-sm transition-all hover:border-red-300 hover:bg-red-100 active:scale-95"
              title="Сбросить все фильтры"
            >
              <X className="h-3.5 w-3.5" />
              Очистить
            </button>
          )}
          {/* Кнопка сортировки */}
          <button
            onClick={onSort}
            className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-black tracking-wider text-slate-600 uppercase shadow-sm transition-all hover:border-slate-300 hover:bg-slate-50 active:scale-95"
          >
            <ArrowUpDown className="h-4 w-4 text-slate-500" />
            {sortOrder === "desc" ? "Сначала новые" : "Сначала старые"}
          </button>

          <CaseNumberSearch
            value={quickCaseNumber}
            direction={direction}
            onChange={onCaseNumberChange}
          />
        </div>

        {/* Счётчик */}
        <p className="px-1 text-[12px] font-bold text-slate-600 uppercase">
          Всего записей:{" "}
          <span className="font-black text-indigo-600">{totalCount}</span>
        </p>
      </div>

      {/* ПРАВЫЙ БЛОК КНОПОК */}
      <div className="flex items-center gap-3">
        {!restricted && (
          <SectionsMenu isSuperadmin={isSuperadmin} direction={direction} />
        )}

        {/* Кнопка экспорта в Excel */}
        {!restricted && (
          <button
            onClick={handleExport}
            disabled={isExporting || exportMock}
            title={exportMock ? "Пока недоступно" : undefined}
            className={`flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-black tracking-wider uppercase shadow-sm transition-all active:scale-95 ${
              isExporting
                ? "cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400"
                : "border-green-200 bg-green-50 text-green-700 hover:border-green-300 hover:bg-green-100"
            }`}
          >
            {isExporting ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-green-700 border-t-transparent"></div>
            ) : (
              <Download className="h-4 w-4" />
            )}
            {isExporting ? "Экспорт..." : "Экспорт в Excel"}
          </button>
        )}

        {/* Кнопка создания */}
        {canCreate && (
          <button
            onClick={onCreate}
            disabled={createDisabled}
            className="flex items-center gap-2 rounded-xl bg-[#0064fe] px-4 py-2.5 text-xs font-black tracking-wider text-white uppercase antialiased shadow-lg shadow-indigo-100 transition-all hover:bg-[#0052cc] hover:shadow-indigo-200 active:scale-95"
          >
            <Plus className="h-4 w-4 stroke-[3px]" />
            Создать
          </button>
        )}
      </div>
    </div>
  );
}
