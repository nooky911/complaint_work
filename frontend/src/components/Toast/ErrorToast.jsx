import React, { useEffect } from "react";
import { X, AlertCircle } from "lucide-react";

export const ErrorToast = ({ show, onClose, title, message }) => {
  useEffect(() => {
    if (show) {
      const timer = setTimeout(() => onClose(), 6000);
      return () => clearTimeout(timer);
    }
  }, [show, onClose]);

  return (
    <div
      className={`fixed top-10 right-10 z-[100] flex transform items-center gap-3 rounded-xl border border-red-100 bg-white p-4 shadow-2xl transition-all duration-300 ${
        show
          ? "translate-x-0 opacity-100"
          : "pointer-events-none translate-x-10 opacity-0"
      }`}
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-500">
        <AlertCircle className="h-6 w-6" />
      </div>
      <div className="max-w-[320px]">
        <p className="text-sm font-bold text-slate-900">
          {title || "Ошибка"}
        </p>
        <p className="mt-1 text-xs text-slate-600 leading-relaxed">
          {message}
        </p>
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
