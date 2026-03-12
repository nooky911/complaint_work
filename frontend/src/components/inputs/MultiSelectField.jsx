import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, Check, Search } from "lucide-react";
import { useDropdown } from "../../hooks/useDropdown";
import { useSearchFilter } from "../../hooks/useSearchFilter";

export const MultiSelectField = ({
  label,
  selectedValues = [],
  options = [],
  onChange,
  placeholder,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const inputRef = useRef(null);
  const { isOpen, setIsOpen, containerRef } = useDropdown(false, () =>
    setSearchTerm(""),
  );
  const filteredOptions = useSearchFilter(options, searchTerm);

  useEffect(() => {
    if (isOpen && inputRef.current) inputRef.current.focus();
  }, [isOpen]);

  const toggleValue = (val) => {
    const isSelected = selectedValues.includes(val);
    const newSelection = isSelected
      ? selectedValues.filter((v) => v !== val)
      : [...selectedValues, val];

    onChange(newSelection);
    setSearchTerm("");
  };

  return (
    <div className="relative w-full" ref={containerRef}>
      <label className="mb-1 ml-1 block text-xs font-bold text-slate-500 uppercase">
        {label}
      </label>

      <div
        onClick={() => setIsOpen(!isOpen)}
        className={`flex h-[38px] cursor-pointer items-center justify-between rounded-lg border border-slate-200 bg-white px-3 shadow-sm transition-all ${
          isOpen
            ? "border-indigo-500 ring-1 ring-indigo-50"
            : "hover:border-slate-400"
        }`}
      >
        <div className="flex items-center overflow-hidden">
          {selectedValues.length === 0 ? (
            <span className="text-sm font-bold text-slate-400">
              {placeholder}
            </span>
          ) : (
            <span className="text-sm font-bold text-slate-800">
              Выбрано: {selectedValues.length}
            </span>
          )}
        </div>
        <ChevronDown
          className={`h-4 w-4 text-slate-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </div>

      {isOpen && (
        <div className="animate-in fade-in zoom-in-95 absolute left-0 z-[120] mt-2 flex max-h-80 w-full flex-col overflow-hidden rounded-xl border border-slate-100 bg-white shadow-2xl duration-200">
          <div className="border-b border-slate-100 p-2">
            <div className="relative">
              <Search className="absolute top-1/2 left-3 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
              <input
                ref={inputRef}
                type="text"
                placeholder="Поиск..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg bg-slate-50 py-2 pr-3 pl-9 text-xs font-bold text-slate-700 outline-none focus:bg-white focus:ring-2 focus:ring-indigo-100"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {filteredOptions.length > 0 ? (
              filteredOptions.map((opt, index) => {
                const isObject = typeof opt === "object";
                const val = isObject ? opt.value || opt.id : opt;
                const name = isObject ? opt.label || opt.name : opt;
                const isSelected = selectedValues.includes(val);

                return (
                  <div
                    key={`${val}-${index}`}
                    onClick={() => toggleValue(val)}
                    className={`flex cursor-pointer items-center justify-between rounded-lg px-3 py-2.5 transition-colors ${
                      isSelected ? "bg-indigo-50" : "hover:bg-slate-50"
                    }`}
                  >
                    <span
                      className={`text-xs font-bold ${isSelected ? "text-indigo-900" : "text-slate-900"}`}
                    >
                      {name}
                    </span>
                    {isSelected && (
                      <Check className="h-4 w-4 text-indigo-600" />
                    )}
                  </div>
                );
              })
            ) : (
              <div className="py-4 text-center text-xs font-medium text-slate-400">
                Ничего не найдено
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
