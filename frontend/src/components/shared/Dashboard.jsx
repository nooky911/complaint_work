import { RepairCaseList } from "../RepairCaseList";
import { CasePagination } from "./CasePagination";

/** Общая страница списка случаев с панелью и формами выбранного направления */
export function Dashboard({
  toolbar,
  cases,
  loading,
  error,
  onRetry,
  restricted = false,
  onCaseClick,
  currentPage,
  totalPages,
  onPageChange,
  children,
}) {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col gap-2 overflow-hidden">
      {toolbar}
      <div className="flex min-h-0 flex-1 flex-col">
        {loading && cases.length === 0 ? (
          <div
            role="status"
            className="flex h-64 animate-pulse flex-col items-center justify-center gap-4"
          >
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
            <span className="text-xs font-black tracking-widest text-slate-400 uppercase">
              Синхронизация данных...
            </span>
          </div>
        ) : error ? (
          <div
            role="alert"
            className="mx-2 rounded-lg bg-red-50 p-3 text-red-700"
          >
            Не удалось загрузить данные.{" "}
            <button onClick={onRetry}>Повторить</button>
          </div>
        ) : (
          <RepairCaseList
            cases={cases}
            restricted={restricted}
            onCaseClick={onCaseClick}
            pagination={
              <CasePagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={onPageChange}
              />
            }
          />
        )}
      </div>
      {children}
    </div>
  );
}
