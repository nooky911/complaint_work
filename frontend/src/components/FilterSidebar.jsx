import React, { useState, useEffect } from "react";

import { useFilterSidebar } from "../hooks/useFilterSidebar";
import { useBodyScrollLock } from "../hooks/useBodyScrollLock";
import { INITIAL_FILTERS } from "../constants/filters";
import {
  FilterSidebarHeader,
  FilterSidebarFooter,
  FilterSectionsRenderer,
} from "./filters";

export const FilterSidebar = ({
  isOpen,
  onClose,
  appliedFilters,
  onApply,
  options,
}) => {
  const [filters, setFilters] = useState(INITIAL_FILTERS);

  const {
    openSections,
    toggleSection,
    mergedOptions,
    hasErrors,
    userOptions,
    getSectionCount,
    sectionThemes,
    isDynamicLoading,
    isDynamicMode,
  } = useFilterSidebar(filters, options);

  useEffect(() => {
    if (isOpen) {
      setFilters({ ...appliedFilters });
    }
  }, [isOpen, appliedFilters]);

  useBodyScrollLock(isOpen);

  const handleUpdateFilter = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleApply = () => {
    onApply(filters);
    onClose();
  };

  const handleReset = () => {
    setFilters(INITIAL_FILTERS);
  };

  const handleClose = () => {
    onClose();
  };

  return (
    <>
      {/* Затемнение фона */}
      <div
        className={`fixed inset-0 z-[100] bg-slate-900/40 backdrop-blur-sm transition-opacity duration-300 ${
          isOpen ? "visible opacity-100" : "invisible opacity-0"
        }`}
      />

      {/* Сайдбар */}
      <div
        className={`fixed inset-y-0 left-0 z-[110] w-[500px] transform bg-white shadow-2xl transition-transform duration-500 ease-out ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <FilterSidebarHeader onClose={handleClose} />

          {/* Body */}
          <div className="flex-1 space-y-3 overflow-y-auto px-6 py-3 text-slate-800">
            {/* Индикатор динамического режима */}
            {isDynamicMode && (
              <div className="mb-4 rounded-lg bg-blue-50 p-3 text-sm text-blue-700">
                {isDynamicLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent"></div>
                    Обновление опций фильтров...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-blue-600"></div>
                    Опции фильтров обновлены на основе выбранных значений
                  </div>
                )}
              </div>
            )}

            <FilterSectionsRenderer
              openSections={openSections}
              toggleSection={toggleSection}
              getSectionCount={(keys) => getSectionCount(keys, filters)}
              sectionThemes={sectionThemes}
              filters={filters}
              options={mergedOptions}
              updateFilter={handleUpdateFilter}
              userOptions={userOptions}
            />
          </div>

          {/* Footer */}
          <FilterSidebarFooter
            onApply={handleApply}
            onReset={handleReset}
            onClose={handleClose}
            hasErrors={hasErrors}
          />
        </div>
      </div>
    </>
  );
};
