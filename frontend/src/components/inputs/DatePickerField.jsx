import React from "react";
import { Calendar } from "lucide-react";
import { useDatePicker } from "../../hooks/useDatePicker";

export const DatePickerField = ({
  label,
  value,
  onChange,
  isEditing,
  isDisabled = false,
  className = "",
  error,
}) => {
  const {
    inputRef,
    setCursorPos,
    handleKeyDown,
    handleTextChange,
    displayValue,
    hasError: dateError,
  } = useDatePicker(value, onChange);

  if (!isEditing) return null;

  const today = new Date().toISOString().split("T")[0];
  const hasError = dateError || error;

  const baseStyles = `w-full h-[38px] rounded-lg border px-3 text-sm font-bold transition-all outline-none ${
    isDisabled
      ? "bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed"
      : hasError
        ? "bg-red-50 text-red-900 border-red-500 focus:border-red-600 shadow-sm"
        : "bg-white text-slate-900 border-gray-200 focus:border-indigo-500 shadow-sm"
  }`;

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <div className="flex items-center justify-between pr-1">
          <label
            className={`mb-1 ml-1 block text-xs font-bold uppercase transition-colors ${hasError ? "text-red-500" : "text-slate-500"}`}
          >
            {label}
          </label>
          {hasError && (
            <span className="mb-1 text-xs font-bold tracking-tight text-red-500 uppercase">
              Ошибка даты
            </span>
          )}
        </div>
      )}
      <div className="relative flex items-center">
        <input
          ref={inputRef}
          type="text"
          value={displayValue}
          onKeyDown={handleKeyDown}
          onChange={handleTextChange}
          disabled={isDisabled}
          className={baseStyles}
        />
        {!isDisabled && (
          <div className="absolute right-3 flex items-center justify-center">
            <Calendar
              className={`pointer-events-none h-4 w-4 transition-colors ${hasError ? "text-red-400" : "text-slate-400"}`}
            />
            <input
              type="date"
              max={today}
              onChange={(e) => {
                setCursorPos(null);
                onChange(e.target.value);
              }}
              className="absolute inset-0 cursor-pointer opacity-0"
              style={{ colorScheme: "light" }}
            />
          </div>
        )}
      </div>
    </div>
  );
};
