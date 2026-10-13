import React from "react";
import { ChevronDown } from "lucide-react";
import { useSearchableSelect } from "../../hooks/useSearchableSelect";

export const SearchableSelect = ({
  options = [],
  value,
  onChange,
  placeholder,
  isDisabled,
  label,
  error,
  onSearchChange,
  onOpen,
  isLoading = false,
  loadError = false,
  onRetry,
  className = "",
}) => {
  const {
    isOpen,
    setIsOpen,
    containerRef,
    searchTerm,
    setSearchTerm,
    selectedOption,
    filteredOptions,
    toggleDropdown,
    handleSelect,
    handleClear,
  } = useSearchableSelect(options, value, onChange);

  const handleToggle = () => {
    if (isDisabled) return;
    if (!isOpen) onOpen?.();
    toggleDropdown();
  };

  return (
    <div className={`flex flex-col gap-1 ${className}`} ref={containerRef}>
      <label className="ml-1 text-xs font-bold tracking-wider text-slate-500 uppercase">
        {label}
      </label>
      <div className="relative">
        <input
          type="text"
          className={`w-full rounded-lg border px-3 py-2 pr-10 text-sm font-bold transition-all outline-none ${
            isDisabled
              ? "cursor-not-allowed border-gray-100 bg-gray-50 text-gray-400"
              : error
                ? "border-red-500 bg-red-50 text-red-900 shadow-sm ring-1 ring-red-100 focus:border-red-600"
                : "cursor-pointer border-gray-200 bg-white text-slate-900 shadow-sm focus:border-indigo-500"
          }`}
          placeholder={placeholder}
          value={isOpen ? searchTerm : selectedOption?.name || ""}
          disabled={isDisabled}
          aria-label={label}
          aria-expanded={isOpen && !isDisabled}
          aria-invalid={!!error}
          autoComplete="off"
          onClick={handleToggle}
          onChange={(e) => {
            if (!isOpen) handleToggle();
            setSearchTerm(e.target.value);
            onSearchChange?.(e.target.value);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape") setIsOpen(false);
            if (event.key === "Enter" && isOpen) {
              event.preventDefault();
              if (!isLoading && !loadError && filteredOptions.length === 1) {
                handleSelect(filteredOptions[0].id, filteredOptions[0].name);
              }
            }
          }}
        />
        <div
          className="absolute inset-y-0 right-0 flex cursor-pointer items-center px-3"
          onClick={(e) => {
            e.stopPropagation();
            handleToggle();
          }}
        >
          <ChevronDown
            className={`h-4 w-4 stroke-[2.5] text-slate-400 transition-transform duration-200 ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </div>
        {isOpen && !isDisabled && (
          <div className="absolute z-[110] mt-1 max-h-60 w-full overflow-auto rounded-xl border border-slate-200 bg-white p-1 shadow-xl">
            <div
              className="mb-1 cursor-pointer rounded-lg border-b border-gray-50 px-3 py-2 text-xs font-bold text-red-500 uppercase transition-colors hover:bg-red-50"
              onClick={handleClear}
            >
              — Сбросить выбор —
            </div>
            {isLoading ? (
              <div className="px-3 py-3 text-center text-xs text-slate-500">Загрузка…</div>
            ) : loadError ? (
              <div className="px-3 py-3 text-center text-xs text-red-700">
                Не удалось загрузить номера
                {onRetry && <button type="button" onClick={onRetry} className="ml-2 underline">Повторить</button>}
              </div>
            ) : filteredOptions.length > 0 ? (
              filteredOptions.map((opt) => (
                <div
                  key={opt.id}
                  className={`cursor-pointer rounded-lg px-3 py-2 text-xs font-bold transition-colors ${
                    value === opt.id
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-slate-900 hover:bg-slate-50"
                  }`}
                  onClick={() => handleSelect(opt.id, opt.name)}
                >
                  {opt.name}
                </div>
              ))
            ) : (
              <div className="px-3 py-2 text-center text-xs text-slate-400 italic">
                Нет совпадений
              </div>
            )}
          </div>
        )}
      </div>
      {typeof error === "string" && <p role="alert" className="text-xs text-red-700">{error}</p>}
    </div>
  );
};
