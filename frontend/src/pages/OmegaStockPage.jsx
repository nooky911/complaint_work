import { useState } from "react";
import {
  ArrowDownToLine,
  ArrowLeft,
  ArrowUpFromLine,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Truck,
  Warehouse,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { StockDocumentTable } from "../components/omegaStock/StockDocumentTable";
import { STOCK_DOCUMENT_TYPES } from "../constants/omegaStockConfig";
import { useOmegaStockDocuments } from "../hooks/api/useOmegaStockApi";

const ICONS = {
  receipts: ArrowDownToLine,
  inplant: Truck,
  outbound: ArrowUpFromLine,
};
const PAGE_SIZE = 50;

export default function OmegaStockPage() {
  const navigate = useNavigate();
  const [kind, setKind] = useState(null);
  const [page, setPage] = useState(1);
  const [expandedDocumentId, setExpandedDocumentId] = useState(null);
  const [filters, setFilters] = useState({});
  const [sort, setSort] = useState(null);
  const selectedType = STOCK_DOCUMENT_TYPES.find((type) => type.key === kind);
  const {
    data: loadedDocuments = [],
    isLoading,
    isError,
    error,
  } = useOmegaStockDocuments(kind, page, PAGE_SIZE, filters, sort);
  const documents = loadedDocuments.slice(0, PAGE_SIZE);
  const hasNextPage = loadedDocuments.length > PAGE_SIZE;

  const selectKind = (nextKind) => {
    setKind(nextKind);
    setPage(1);
    setExpandedDocumentId(null);
    setFilters({});
    setSort(null);
  };

  const applySort = (column) => {
    setSort((current) => ({
      column,
      direction:
        current?.column === column && current.direction === "asc"
          ? "desc"
          : "asc",
    }));
    setPage(1);
    setExpandedDocumentId(null);
  };

  const applyFilter = (column, selection) => {
    setFilters((current) => {
      const next = { ...current };
      if (selection) next[column] = selection;
      else delete next[column];
      return next;
    });
    setPage(1);
    setExpandedDocumentId(null);
  };

  const errorMessage =
    typeof error?.response?.data?.detail === "string"
      ? error.response.data.detail
      : "Не удалось загрузить документы из Omega";

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-4 border-b border-gray-200 bg-white px-6 py-4">
        <button
          type="button"
          onClick={() => (kind ? selectKind(null) : navigate("/"))}
          className="flex items-center gap-2 text-gray-600 transition-colors hover:text-gray-900"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Назад</span>
        </button>
        <h1 className="text-xl font-semibold text-gray-900">
          {selectedType?.title ?? "Склад"}
        </h1>
      </div>

      <div className="min-h-0 flex-1 overflow-auto bg-gray-50 p-6">
        <div
          className={`mx-auto flex w-full flex-col gap-5 ${
            kind ? "max-w-none" : "max-w-7xl"
          }`}
        >
          {!kind ? (
            <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                  <Warehouse className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-base font-black text-slate-900">
                    Выберите вид документов
                  </h2>
                  <p className="text-xs text-slate-500">
                    Сведения загружаются из Omega для просмотра
                  </p>
                </div>
              </div>
              <div className="grid gap-3 md:grid-cols-3">
                {STOCK_DOCUMENT_TYPES.map((type) => {
                  const Icon = ICONS[type.key];
                  return (
                    <button
                      key={type.key}
                      type="button"
                      onClick={() => selectKind(type.key)}
                      className="group flex flex-col items-start gap-3 rounded-xl border border-slate-200 bg-white p-5 text-left transition-colors hover:border-indigo-300 hover:bg-indigo-50"
                    >
                      <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600 group-hover:bg-white">
                        <Icon className="h-5 w-5" />
                      </div>
                      <span className="text-sm font-black text-slate-900">
                        {type.title}
                      </span>
                      <span className="text-xs leading-5 text-slate-500">
                        {type.description}
                      </span>
                    </button>
                  );
                })}
              </div>
            </section>
          ) : (
            <section className="rounded-xl border border-gray-200 bg-white shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
                <div>
                  <h2 className="text-sm font-black text-slate-900">
                    {selectedType.title}
                  </h2>
                  <p className="mt-1 text-xs text-slate-500">
                    Нажмите на строку, чтобы открыть состав документа
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={() => { setFilters({}); setPage(1); setExpandedDocumentId(null); }}
                    disabled={Object.keys(filters).length === 0}
                    className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    Сбросить фильтры
                  </button>
                  <button
                    type="button"
                    onClick={() => selectKind(null)}
                    className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"
                  >
                    Другой вид документов
                  </button>
                </div>
              </div>

              {isLoading ? (
                <div className="flex h-56 items-center justify-center gap-3 text-xs font-black tracking-wider text-slate-400 uppercase">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
                  Загрузка документов...
                </div>
              ) : isError ? (
                <div className="m-5 rounded-lg bg-red-50 px-4 py-3 text-sm font-semibold text-red-600">
                  {errorMessage}
                </div>
              ) : (
                <StockDocumentTable
                  kind={kind}
                  documents={documents}
                  expandedDocumentId={expandedDocumentId}
                  onSelect={(documentId) =>
                    setExpandedDocumentId((current) =>
                      current === documentId ? null : documentId,
                    )
                  }
                  filters={filters}
                  onFilterChange={applyFilter}
                  sort={sort}
                  onSortChange={applySort}
                />
              )}

              {!isError && !isLoading && (page > 1 || hasNextPage) && (
                <div className="flex items-center justify-end gap-3 border-t border-slate-100 px-5 py-3 text-xs font-bold text-slate-600">
                  <button
                    type="button"
                    onClick={() => { setPage((current) => current - 1); setExpandedDocumentId(null); }}
                    disabled={page === 1}
                    aria-label="Предыдущая страница"
                    className="rounded-lg p-2 hover:bg-slate-100 disabled:opacity-30"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  Страница {page}
                  <button
                    type="button"
                    onClick={() => { setPage((current) => current + 1); setExpandedDocumentId(null); }}
                    disabled={!hasNextPage}
                    aria-label="Следующая страница"
                    className="rounded-lg p-2 hover:bg-slate-100 disabled:opacity-30"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
