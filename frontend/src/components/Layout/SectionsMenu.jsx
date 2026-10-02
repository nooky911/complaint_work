import { useEffect, useRef, useState } from "react";
import {
  BookOpenText,
  ChevronDown,
  Layers3,
  Settings,
  Warehouse,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

export function SectionsMenu({ isSuperadmin }) {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const closeOutside = (event) => {
      if (!menuRef.current?.contains(event.target)) setIsOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setIsOpen(false);
    };

    document.addEventListener("mousedown", closeOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, []);

  const openSection = (path) => {
    setIsOpen(false);
    navigate(path);
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        onClick={() => setIsOpen((current) => !current)}
        className="flex items-center justify-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2.5 text-xs font-black tracking-wider text-indigo-600 uppercase shadow-sm transition-all hover:border-indigo-300 hover:bg-indigo-100 active:scale-95"
      >
        <Layers3 className="h-4 w-4" />
        Разделы
        <ChevronDown
          className={`h-3.5 w-3.5 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      {isOpen && (
        <div
          role="menu"
          className="absolute top-full right-0 z-50 mt-2 w-52 rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl"
        >
          <button
            type="button"
            role="menuitem"
            onClick={() => openSection("/product-passports")}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-semibold text-slate-700 hover:bg-indigo-50 hover:text-indigo-700"
          >
            <BookOpenText className="h-4 w-4" />
            Паспорта
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => openSection("/omega-stock")}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-semibold text-slate-700 hover:bg-indigo-50 hover:text-indigo-700"
          >
            <Warehouse className="h-4 w-4" />
            Склад
          </button>
          {isSuperadmin && (
            <button
              type="button"
              role="menuitem"
              onClick={() => openSection("/equipment-management")}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-semibold text-slate-700 hover:bg-indigo-50 hover:text-indigo-700"
            >
              <Settings className="h-4 w-4" />
              Оборудование
            </button>
          )}
        </div>
      )}
    </div>
  );
}
