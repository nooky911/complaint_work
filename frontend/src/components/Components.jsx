import React, { useRef, useEffect } from "react";

// Автоматически расширяемое текстовое поле
export const AutoResizingTextarea = ({
  label,
  value,
  onChange,
  isDisabled,
  placeholder = "-",
  className = "",
}) => {
  const textareaRef = useRef(null);

  // Логика авто-высоты
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);

  return (
    <div className="flex w-full flex-col">
      {label && (
        <label className="mb-1 ml-1 block text-xs font-bold text-slate-500 uppercase">
          {label}
        </label>
      )}
      <textarea
        ref={textareaRef}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={isDisabled}
        rows={1}
        className={`min-h-[38px] w-full resize-none overflow-hidden rounded-lg border px-3 py-2 text-sm font-bold transition-all outline-none ${
          isDisabled
            ? "cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400"
            : "border-gray-200 bg-white text-slate-900 shadow-sm focus:border-indigo-500"
        } ${className}`}
      />
    </div>
  );
};

export function TabButton({ active, onClick, label }) {
  return (
    <button
      onClick={onClick}
      className={`relative pb-3 text-xs font-black tracking-widest uppercase transition-colors ${
        active ? "text-blue-600" : "text-slate-400 hover:text-slate-600"
      }`}
    >
      {label}
      {active && (
        <div className="absolute right-0 bottom-0 left-0 h-0.5 rounded-full bg-blue-600" />
      )}
    </button>
  );
}
