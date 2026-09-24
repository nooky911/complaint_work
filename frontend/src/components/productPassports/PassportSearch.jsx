import { useEffect, useRef, useState } from "react";
import { ChevronDown, Search } from "lucide-react";

import { useProductPassportSearch } from "../../hooks/api/index.jsx";
import { useDebouncedValue } from "../../hooks/useDebounce";

export function PassportSearch({
  models,
  selectedModelId,
  onModelChange,
  onPassportSelect,
}) {
  const [number, setNumber] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);
  const debouncedNumber = useDebouncedValue(number, 300);
  const { data: passports = [], isFetching } = useProductPassportSearch(
    selectedModelId,
    debouncedNumber,
  );

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!containerRef.current?.contains(event.target)) setIsOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleModelChange = (event) => {
    setNumber("");
    setIsOpen(false);
    onPassportSelect(null);
    onModelChange(event.target.value ? Number(event.target.value) : null);
  };

  const handleNumberChange = (event) => {
    setNumber(event.target.value);
    setIsOpen(true);
    onPassportSelect(null);
  };

  const handleSelect = (passport) => {
    setNumber(passport.product_number);
    setIsOpen(false);
    onPassportSelect(passport.id);
  };

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <div className="flex flex-col gap-1">
        <label className="ml-1 text-xs font-bold tracking-wider text-slate-500 uppercase">
          Модель локомотива
        </label>
        <div className="relative">
          <select
            value={selectedModelId || ""}
            onChange={handleModelChange}
            className="w-full appearance-none rounded-lg border border-gray-200 bg-white px-3 py-2.5 pr-10 text-sm font-bold text-slate-900 shadow-sm transition-all outline-none focus:border-indigo-500"
          >
            <option value="">Выберите модель</option>
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute top-1/2 right-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
        </div>
      </div>

      <div className="relative flex flex-col gap-1" ref={containerRef}>
        <label className="ml-1 text-xs font-bold tracking-wider text-slate-500 uppercase">
          Номер локомотива
        </label>
        <div className="relative">
          <input
            type="text"
            value={number}
            onChange={handleNumberChange}
            onFocus={() => number.trim() && setIsOpen(true)}
            disabled={!selectedModelId}
            placeholder={
              selectedModelId
                ? "Начните вводить номер"
                : "Сначала выберите модель"
            }
            autoComplete="off"
            className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 pr-10 text-sm font-bold text-slate-900 shadow-sm transition-all outline-none placeholder:font-normal placeholder:text-slate-400 focus:border-indigo-500 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-400"
          />
          {isFetching ? (
            <div className="absolute top-1/2 right-3 h-4 w-4 -translate-y-1/2 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          ) : (
            <Search className="absolute top-1/2 right-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
          )}
        </div>

        {isOpen && debouncedNumber.trim() && (
          <div className="absolute top-full z-20 mt-1 max-h-64 w-full overflow-auto rounded-xl border border-slate-200 bg-white p-1 shadow-xl">
            {passports.length ? (
              passports.map((passport) => (
                <button
                  key={passport.id}
                  type="button"
                  onClick={() => handleSelect(passport)}
                  className="flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-indigo-50"
                >
                  <span className="text-sm font-black text-slate-900">
                    №{passport.product_number}
                  </span>
                  <span className="ml-3 truncate text-xs text-slate-500">
                    {passport.omega_name}
                  </span>
                </button>
              ))
            ) : !isFetching ? (
              <div className="px-3 py-4 text-center text-xs font-medium text-slate-400">
                Паспорт с таким номером не найден
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
