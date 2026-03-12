import React, { useEffect } from "react";
import { X, FileWarning } from "lucide-react";

export const FileValidationToast = ({ show, onClose, errors }) => {
  useEffect(() => {
    if (show) {
      const timer = setTimeout(() => onClose(), 6000);
      return () => clearTimeout(timer);
    }
  }, [show, onClose]);

  if (!errors || errors.length === 0) return null;

  return (
    <div
      className={`fixed top-10 right-10 z-[100] flex transform items-start gap-3 rounded-xl border border-amber-100 bg-white p-4 shadow-2xl transition-all duration-300 ${
        show
          ? "translate-x-0 opacity-100"
          : "pointer-events-none translate-x-10 opacity-0"
      }`}
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-600">
        <FileWarning className="h-6 w-6" />
      </div>
      <div className="max-w-[320px]">
        <p className="text-sm font-semibold text-red-700">Ошибка загрузки файлов:</p>
        <ul className="mt-2 list-disc pl-5 text-xs text-slate-600 space-y-1">
          {errors.map((error, idx) => (
            <li key={idx} className="leading-snug">
              {typeof error === 'string' ? error : error?.msg || JSON.stringify(error)}
            </li>
          ))}
        </ul>
      </div>
      <button
        onClick={onClose}
        className="ml-2 text-slate-400 hover:text-slate-600"
      >
        <X size={16} />
      </button>
    </div>
  );
};
