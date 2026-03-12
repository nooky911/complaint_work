import React from "react";
import { RotateCcw, X } from "lucide-react";

export const FilterSidebarFooter = ({ onApply, onReset, onClose, hasErrors }) => {
  return (
    <div className="border-t border-slate-100 bg-slate-100/50 px-8 py-4">
      <div className="flex items-center gap-3">
        <button
          onClick={onReset}
          className="flex h-[42px] flex-1 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white text-[11px] font-bold text-slate-500 transition-all hover:bg-red-50 hover:text-red-600 active:scale-[0.98]"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          ОЧИСТИТЬ
        </button>

        <button
          onClick={onClose}
          className="flex h-[42px] items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 text-[11px] font-bold text-slate-500 transition-all hover:bg-slate-50 active:scale-[0.98]"
        >
          <X className="h-3.5 w-3.5" />
          ЗАКРЫТЬ
        </button>

        <button
          onClick={onApply}
          disabled={hasErrors}
          className={`h-[42px] flex-[2] rounded-lg text-xs font-black tracking-widest text-white uppercase shadow-md transition-all ${
            hasErrors
              ? "cursor-not-allowed bg-slate-300 opacity-80 shadow-none"
              : "bg-indigo-600 shadow-indigo-100 hover:bg-indigo-700 active:scale-[0.98]"
          }`}
        >
          {hasErrors ? "ОШИБКА" : "ПРИМЕНИТЬ"}
        </button>
      </div>
    </div>
  );
};
