import React from "react";
import { X } from "lucide-react";

export const FilterSidebarHeader = ({ onClose }) => {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
      <h3 className="text-lg font-bold tracking-tighter text-slate-800 uppercase">
        Параметры поиска
      </h3>
      <button
        onClick={onClose}
        className="rounded-full bg-slate-100 p-2 text-slate-500 hover:bg-red-50 hover:text-red-500"
      >
        <X className="h-5 w-5" />
      </button>
    </div>
  );
};
