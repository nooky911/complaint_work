import React from "react";
import { useEditableField } from "../../hooks/useEditableField";

export const EditableField = ({
  label,
  value,
  isEditing,
  onChange,
  type = "text",
  placeholder = "",
  className = "",
  isDisabled = false,
  error,
}) => {
  const { handleChange, displayValue } = useEditableField(value, onChange, type);

  if (!isEditing) return null;

  const baseStyles = `w-full h-[38px] rounded-lg border px-3 text-sm font-bold transition-all outline-none ${
    isDisabled
      ? "bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed"
      : error
        ? "bg-red-50 text-red-900 border-red-500 focus:border-red-600 shadow-sm"
        : "bg-white text-slate-900 border-gray-200 focus:border-indigo-500 shadow-sm"
  }`;

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label className="mb-1 ml-1 block text-xs font-bold text-slate-500 uppercase">
          {label}
        </label>
      )}
      {type === "textarea" ? (
        <textarea
          value={displayValue}
          disabled={isDisabled}
          onChange={handleChange}
          placeholder={placeholder}
          className={`min-h-[80px] resize-y ${baseStyles}`}
        />
      ) : (
        <input
          type={type === "number" ? "number" : "text"}
          value={displayValue}
          disabled={isDisabled}
          onChange={handleChange}
          placeholder={placeholder}
          className={`${baseStyles} ${
            type === "number"
              ? "[appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
              : ""
          }`}
        />
      )}
    </div>
  );
};
