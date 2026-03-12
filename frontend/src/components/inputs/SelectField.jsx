import React from "react";
import { ChevronDown } from "lucide-react";
import { useSelectField } from "../../hooks/useSelectField";

export const SelectField = ({
  label,
  value,
  options,
  isEditing,
  onChange,
  placeholder = "—",
  className = "",
  disabled = false,
  error,
}) => {
  const { handleChange, displayValue } = useSelectField(value, onChange);

  if (!isEditing) return null;

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label className="mb-1 ml-1 block text-xs font-bold text-slate-500 uppercase">
          {label}
        </label>
      )}
      <div className="relative">
        <select
          value={displayValue}
          disabled={disabled}
          onChange={handleChange}
          className={`w-full cursor-pointer appearance-none rounded-lg border px-3 py-2 pr-10 text-sm font-bold shadow-sm transition-all outline-none ${
            error
              ? "border-red-500 bg-red-50 text-red-900 focus:border-red-600"
              : "border-gray-200 bg-white text-slate-900 focus:border-indigo-500"
          } disabled:bg-gray-50`}
        >
          <option value="">{placeholder}</option>
          {options?.map((opt) => (
            <option key={opt.id} value={opt.id}>
              {opt.name}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3">
          <ChevronDown className="h-4 w-4 stroke-[2.5] text-slate-400" />
        </div>
      </div>
    </div>
  );
};
