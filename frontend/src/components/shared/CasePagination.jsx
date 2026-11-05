import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

/** Общая пагинация с переходом по номеру страницы */
export function CasePagination({ currentPage, totalPages, onPageChange }) {
  const [isEditingPage, setIsEditingPage] = useState(false);
  const [pageInput, setPageInput] = useState("");
  return (
    <div className="flex w-fit items-center gap-1 p-1 select-none">
      {/* Кнопка Назад */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onPageChange((p) => Math.max(1, p - 1));
        }}
        disabled={currentPage === 1}
        aria-label="Предыдущая страница"
        className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-slate-200/60 disabled:opacity-30 disabled:hover:bg-transparent"
      >
        <ChevronLeft className="h-5 w-5" />
      </button>

      {/* Цифры страниц */}
      <div className="flex items-center gap-1">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onPageChange(1);
          }}
          className={`h-8 min-w-[2rem] rounded-lg px-2 text-xs font-black transition-colors ${
            currentPage === 1
              ? "bg-indigo-600 text-white shadow-md"
              : "text-slate-600 hover:bg-slate-200/60"
          }`}
        >
          1
        </button>

        {currentPage > 3 && (
          <span className="flex h-8 w-6 items-center justify-center text-xs tracking-widest text-slate-400">
            ...
          </span>
        )}

        {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => {
          if (
            p > 1 &&
            p < totalPages &&
            p >= currentPage - 1 &&
            p <= currentPage + 1
          ) {
            return (
              <button
                key={p}
                onClick={(e) => {
                  e.stopPropagation();
                  onPageChange(p);
                }}
                className={`h-8 min-w-[2rem] rounded-lg px-2 text-xs font-black transition-colors ${
                  currentPage === p
                    ? "bg-indigo-600 text-white shadow-md"
                    : "text-slate-600 hover:bg-slate-200/60"
                }`}
              >
                {p}
              </button>
            );
          }
          return null;
        })}

        {/* Ручной ввод страниц */}
        {currentPage < totalPages - 2 &&
          (isEditingPage ? (
            <input
              type="number"
              autoFocus
              placeholder="№"
              className="h-8 w-12 rounded-lg border-2 border-indigo-400 bg-white px-1 text-center text-sm font-bold text-slate-900 shadow-sm outline-none focus:ring-0"
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              onBlur={() => setIsEditingPage(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  const p = parseInt(pageInput, 10);
                  if (p > 0 && p <= totalPages) onPageChange(p);
                  setIsEditingPage(false);
                  setPageInput("");
                }
              }}
            />
          ) : (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setPageInput("");
                setIsEditingPage(true);
              }}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-xs font-black tracking-widest text-slate-400 transition-colors hover:bg-slate-200/60 hover:text-indigo-600"
              title="Ввести номер страницы..."
            >
              ...
            </button>
          ))}

        {totalPages > 1 && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onPageChange(totalPages);
            }}
            className={`h-8 min-w-[2rem] rounded-lg px-2 text-xs font-black transition-colors ${
              currentPage === totalPages
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-600 hover:bg-slate-200/60"
            }`}
          >
            {totalPages}
          </button>
        )}
      </div>

      {/* Кнопка Вперед */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onPageChange((p) => Math.min(totalPages, p + 1));
        }}
        disabled={currentPage === totalPages}
        aria-label="Следующая страница"
        className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-slate-200/60 disabled:opacity-30 disabled:hover:bg-transparent"
      >
        <ChevronRight className="h-5 w-5" />
      </button>
    </div>
  );
}
