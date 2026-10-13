import React, { useMemo } from "react";
import { ChevronDown, Check } from "lucide-react";
import { formatSectionMask } from "../../utils/formatters";
import { SECTIONS_CONFIG } from "../../constants/sections_mask";
import { useDropdown } from "../../hooks/useDropdown";

export const SectionSelect = ({
  label,
  isEditing,
  mask,
  onChange,
  className = "",
  error,
  isDisabled = false,
  availableMask = 7,
}) => {
  const { isOpen, setIsOpen, containerRef } = useDropdown();

  const toggleBit = (bit) => {
    if (!isDisabled && (availableMask & bit)) onChange((mask || 0) ^ bit);
  };
  const isSelected = (bit) => !!(mask & bit);

  const displayValue = useMemo(() => {
    const formatted = formatSectionMask(mask);
    return formatted === "—" ? "—" : formatted;
  }, [mask]);

  if (!isEditing) return null;

  return (
    <div className={`relative w-full ${className}`} ref={containerRef}>
      {label && (
        <label className="mb-1 ml-1 block text-xs font-bold text-slate-500 uppercase">
          {label}
        </label>
      )}
      <div
        role="button"
        aria-label={label}
        aria-disabled={isDisabled}
        tabIndex={isDisabled ? -1 : 0}
        onClick={() => { if (!isDisabled) setIsOpen(!isOpen); }}
        onKeyDown={(event) => {
          if (!isDisabled && (event.key === "Enter" || event.key === " ")) {
            event.preventDefault();
            setIsOpen(!isOpen);
          }
        }}
        className={`flex h-[38px] items-center justify-between rounded-lg border px-3 shadow-sm transition-all ${
          isDisabled ? "cursor-not-allowed border-gray-100 bg-gray-50" : error
            ? "border-red-500 bg-red-50 shadow-red-50"
            : isOpen
              ? "border-indigo-500 ring-1 ring-indigo-50"
              : "border-slate-200 bg-white hover:border-slate-400"
        }`}
      >
        <span
          className={`text-sm font-bold ${isDisabled ? "text-gray-400" : error ? "text-red-900" : displayValue === "Все" ? "text-slate-400" : "text-slate-800"}`}
        >
          {displayValue}
        </span>
        <ChevronDown
          className={`h-4 w-4 text-slate-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </div>

      {isOpen && !isDisabled && (
        <div className="animate-in fade-in zoom-in-95 absolute left-0 z-[120] mt-2 w-full overflow-hidden rounded-xl border border-slate-100 bg-white p-2 shadow-2xl duration-200">
          <div className="space-y-1">
            {SECTIONS_CONFIG.filter((s) => availableMask & s.bit).map((s) => (
              <div
                key={s.bit}
                onClick={() => toggleBit(s.bit)}
                className={`flex cursor-pointer items-center justify-between rounded-lg px-3 py-2.5 transition-colors ${
                  isSelected(s.bit) ? "bg-indigo-50" : "hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-4 w-4 items-center justify-center rounded border transition-all ${
                      isSelected(s.bit)
                        ? "border-indigo-600 bg-indigo-600 shadow-sm"
                        : "border-slate-300 bg-white"
                    }`}
                  >
                    {isSelected(s.bit) && (
                      <Check className="h-3 w-3 stroke-[3] text-white" />
                    )}
                  </div>
                  <span
                    className={`text-xs font-bold ${
                      isSelected(s.bit) ? "text-indigo-900" : "text-slate-600"
                    }`}
                  >
                    Секция {s.label}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-2 border-t border-slate-50 pt-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsOpen(false);
              }}
              className="flex w-full items-center justify-center rounded-lg bg-indigo-600 py-2 text-xs font-bold text-white transition-all hover:bg-indigo-700 active:scale-[0.97]"
            >
              Готово
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
