import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Filter, Search } from "lucide-react";

import { useOmegaStockFilterOptions } from "../../hooks/api/useOmegaStockApi";
import { formatOmegaStockValue } from "../../utils/omegaStockFormatters";

const MAX_VISIBLE_OPTIONS = 200;

const labelFor = (value, format) => {
  if (value === null) return "(Пустые)";
  if (format === "files") return value === "1" ? "Есть" : "Нет";
  return formatOmegaStockValue(value, format);
};

export function StockColumnFilter({ kind, column, filters, onChange }) {
  const buttonRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);
  const otherFilters = useMemo(() => {
    const next = { ...filters };
    delete next[column.key];
    return next;
  }, [filters, column.key]);
  const { data: options = [], isLoading, isError, refetch } =
    useOmegaStockFilterOptions(kind, column.key, otherFilters, open);

  useEffect(() => {
    if (!open || selected !== null || isLoading || isError) return;
    const current = filters[column.key];
    setSelected(new Set(options.filter((value) => {
      if (!current) return true;
      const contains = current.values.includes(value);
      return current.mode === "include" ? contains : !contains;
    })));
  }, [open, selected, isLoading, isError, options, filters, column.key]);

  useEffect(() => {
    if (!open) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [open]);

  const openMenu = () => {
    if (open) { setOpen(false); return; }
    const rect = buttonRef.current.getBoundingClientRect();
    const width = Math.min(320, window.innerWidth - 16);
    setPosition({
      left: Math.max(8, Math.min(rect.left, window.innerWidth - width - 8)),
      top: rect.bottom + 8 + 350 > window.innerHeight
        ? Math.max(8, rect.top - 358)
        : rect.bottom + 8,
    });
    setSearch("");
    setSelected(null);
    setOpen(true);
  };

  const matching = options.filter((value) =>
    labelFor(value, column.format).toLocaleLowerCase("ru").includes(search.toLocaleLowerCase("ru")),
  );
  const allMatchingSelected = matching.length > 0 && matching.every((value) => selected?.has(value));
  const someMatchingSelected = matching.some((value) => selected?.has(value));

  const toggleValue = (value) => {
    setSelected((current) => {
      const next = new Set(current ?? []);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  };

  const toggleMatching = () => {
    setSelected((current) => {
      const next = new Set(current ?? []);
      for (const value of matching) {
        if (allMatchingSelected) next.delete(value);
        else next.add(value);
      }
      return next;
    });
  };

  const apply = () => {
    if (selected === null) return;
    const excluded = options.filter((value) => !selected.has(value));
    if (excluded.length === 0) onChange(null);
    else if (selected.size <= excluded.length) {
      onChange({ mode: "include", values: options.filter((value) => selected.has(value)) });
    } else {
      onChange({ mode: "exclude", values: excluded });
    }
    setOpen(false);
  };

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        onClick={openMenu}
        aria-label={`Фильтр: ${column.title}`}
        aria-expanded={open}
        className={`relative -top-px ml-0.5 inline-flex items-center justify-center align-middle rounded p-0 transition-colors hover:bg-indigo-100 hover:text-indigo-700 ${filters[column.key] ? "bg-indigo-100 text-indigo-700" : "text-slate-400"}`}
      >
        <Filter className="h-2.5 w-2.5" />
      </button>
      {open && createPortal(
        <>
          <div className="fixed inset-0 z-[100]" onClick={() => setOpen(false)} />
          <div
            role="dialog"
            aria-label={`Фильтр: ${column.title}`}
            className="fixed z-[101] flex w-[min(320px,calc(100vw-16px))] flex-col rounded-xl border border-slate-200 bg-white p-3 text-left text-xs normal-case tracking-normal shadow-2xl"
            style={position}
          >
            <div className="mb-2 font-bold text-slate-800">{column.title}</div>
            <div className="relative mb-2">
              <Search className="absolute top-2.5 left-2.5 h-4 w-4 text-slate-400" />
              <input
                autoFocus
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Поиск"
                className="w-full rounded-lg border border-slate-200 py-2 pr-2 pl-8 text-sm text-slate-800 outline-none focus:border-indigo-400"
              />
            </div>
            {isLoading ? (
              <div className="py-8 text-center text-slate-500">Загрузка значений...</div>
            ) : isError ? (
              <div className="py-5 text-center text-red-600">
                Не удалось загрузить значения
                <button type="button" onClick={() => refetch()} className="ml-2 underline">Повторить</button>
              </div>
            ) : (
              <>
                <label className="flex cursor-pointer items-center gap-2 border-b border-slate-100 px-1 py-2 font-semibold text-slate-700">
                  <input
                    type="checkbox"
                    checked={allMatchingSelected}
                    ref={(element) => { if (element) element.indeterminate = someMatchingSelected && !allMatchingSelected; }}
                    onChange={toggleMatching}
                    disabled={matching.length === 0 || selected === null}
                    className="accent-indigo-600"
                  />
                  Выделить все {search && "найденные"}
                </label>
                <div className="max-h-64 min-h-24 overflow-y-auto py-1">
                  {matching.slice(0, MAX_VISIBLE_OPTIONS).map((value) => (
                    <label key={value ?? "__empty__"} className="flex cursor-pointer items-start gap-2 rounded px-1 py-1.5 text-slate-700 hover:bg-indigo-50">
                      <input
                        type="checkbox"
                        checked={selected?.has(value) ?? false}
                        onChange={() => toggleValue(value)}
                        className="mt-0.5 accent-indigo-600"
                      />
                      <span className="break-all">{labelFor(value, column.format)}</span>
                    </label>
                  ))}
                  {matching.length === 0 && <div className="px-1 py-4 text-center text-slate-500">Ничего не найдено</div>}
                </div>
                {matching.length > MAX_VISIBLE_OPTIONS && (
                  <div className="border-t border-slate-100 py-2 text-slate-500">
                    Показаны первые {MAX_VISIBLE_OPTIONS} из {matching.length}. Уточните поиск. «Выделить все» учитывает весь список.
                  </div>
                )}
                <div className="mt-2 flex justify-end gap-2 border-t border-slate-100 pt-3">
                  <button type="button" onClick={() => setOpen(false)} className="rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100">Отмена</button>
                  <button type="button" onClick={apply} disabled={selected === null} className="rounded-lg bg-indigo-600 px-4 py-2 font-bold text-white hover:bg-indigo-700 disabled:opacity-40">ОК</button>
                </div>
              </>
            )}
          </div>
        </>, document.body,
      )}
    </>
  );
}
