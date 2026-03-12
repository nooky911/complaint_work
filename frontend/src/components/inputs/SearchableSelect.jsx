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
}) => {
  const {
    isOpen,
    containerRef,
    searchTerm,
    setSearchTerm,
    selectedOption,
    filteredOptions,
    toggleDropdown,
    handleSelect,
    handleClear,
  } = useSearchableSelect(options, value, onChange);

  return (
    <div className="flex flex-col gap-1" ref={containerRef}>
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
          onClick={toggleDropdown}
          onChange={(e) => {
            if (!isOpen) toggleDropdown();
            setSearchTerm(e.target.value);
          }}
        />
        <div
          className="absolute inset-y-0 right-0 flex cursor-pointer items-center px-3"
          onClick={(e) => {
            e.stopPropagation();
            toggleDropdown();
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
            {filteredOptions.length > 0 ? (
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
    </div>
  );
};
