import React, { useEffect } from "react";
import { AlertCircle, X } from "lucide-react";

export const CaseValidationToast = ({ show, onClose, validation }) => {
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
      <div className="max-w-[250px]">
        <p className="text-sm font-bold text-slate-900">
          Не все поля заполнены:
        </p>
        <ul className="mt-1 list-disc pl-4 text-[11px] leading-tight font-medium text-slate-500">
          {validation.dateError && (
            <li>Некорректный формат дат или нет даты отказа</li>
          )}
          {validation.isFaultDateMissing && <li>Укажите дату неисправности</li>}
          {validation.isSectionMissing && <li>Укажите секцию</li>}
          {validation.isRegionMissing && <li>Выберите региональный центр</li>}
          {validation.isLocoModelMissing && <li>Выберите модель локомотива</li>}
          {validation.isDiscoveredAtMissing && <li>Укажите, где выявлено</li>}
          {validation.isRepairTypeMissing && <li>Укажите тип ремонта</li>}
          {validation.isQuantityInvalid && <li>Кол-во должно быть ≥ 1</li>}
          {validation.isDesignationMissing && (
            <li>Выберите оборудование (до Обозначения)</li>
          )}
          {validation.isMalfunctionMissing && <li>Выберите неисправность</li>}
          {validation.isRepairTypeBlocked && (
            <li>Тип ремонта не подходит к оборудованию</li>
          )}
          {validation.isNewComponentMissing && (
            <li>Укажите новое оборудование (Обозначение)</li>
          )}
          {validation.isNewElementMissing && (
            <li>Укажите новый элемент оборудования</li>
          )}
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
