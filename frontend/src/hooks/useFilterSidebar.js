import { useState, useEffect, useMemo, useRef } from "react";
import { validateFilterDates } from "../utils/validators";
import { formatFullName } from "../utils/formatters";
import { FILTER_DATE_FIELDS } from "../constants/filters";
import { useDynamicFilterOptions } from "./api/index.jsx";

// Debounce хук
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

export const useFilterSidebar = (filters, options) => {
  const [openSections, setOpenSections] = useState({
    locomotive: false,
    equipment: false,
    repair: false,
    status: false,
    documents: false,
    suppliers: false,
  });

  const [dynamicOptions, setDynamicOptions] = useState(null);
  const [isDynamicMode, setIsDynamicMode] = useState(false);

  const frozenOptionsRef = useRef({});

  const debouncedFilters = useDebounce(filters, 500);

  const activeKeysInstant = useMemo(() => {
    return Object.keys(filters).filter((key) => {
      const val = filters[key];
      if (Array.isArray(val)) return val.length > 0;
      return val !== "" && val !== null && val !== undefined && val !== 0;
    });
  }, [filters]);

  const hasActiveFilters = useMemo(() => {
    return Object.entries(debouncedFilters).some(([key, value]) => {
      if (key === "skip" || key === "limit") return false;
      if (Array.isArray(value)) return value.length > 0;
      return (
        value !== "" && value !== null && value !== undefined && value !== 0
      );
    });
  }, [debouncedFilters]);

  useEffect(() => {
    setIsDynamicMode(hasActiveFilters);
  }, [hasActiveFilters]);

  const { data: dynamicOptionsData, isLoading: isDynamicLoading } =
    useDynamicFilterOptions(debouncedFilters);

  useEffect(() => {
    if (dynamicOptionsData) {
      setDynamicOptions(dynamicOptionsData);
    }
  }, [dynamicOptionsData]);

  useEffect(() => {
    if (!hasActiveFilters) {
      setDynamicOptions(null);
    }
  }, [hasActiveFilters]);

  const toggleSection = (section) => {
    setOpenSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const updateFilter = (key, value) => {
    return { key, value };
  };

  const hasErrors = validateFilterDates(filters, FILTER_DATE_FIELDS);

  const userOptions =
    options?.users?.map((user) => ({
      ...user,
      name: formatFullName(user.name),
    })) || [];

  const mergedOptions = useMemo(() => {
    const currentDynamic = dynamicOptions || {};
    const merged = { ...options };

    const optionsToFiltersMap = {
      locomotive_models: "locomotive_model_id",
      locomotive_numbers: "locomotive_number",
      regional_centers: "regional_center_id",
      equipment_types: "equipment_type_id",
      malfunction_types: "malfunction_id",
      repair_types: "repair_type_id",
      equipment_owners: "equipment_owner_id",
      performed_by: "performed_by_id",
      destinations: "destination_id",
      components: "component_equipment_id",
      elements: "element_equipment_id",
      new_components: "new_component_equipment_id",
      new_elements: "new_element_equipment_id",
      suppliers: "supplier_id",
      statuses: "status",
      malfunctions: "malfunction_id",
      component_serial_numbers: "component_serial_number_old",
      element_serial_numbers: "element_serial_number_old",
      component_serial_numbers_new: "component_serial_number_new",
      element_serial_numbers_new: "element_serial_number_new",
    };

    Object.keys(options).forEach((key) => {
      const filterKey = optionsToFiltersMap[key] || key;
      const isBeingEdited = activeKeysInstant.includes(filterKey);

      if (isBeingEdited) {
        if (!frozenOptionsRef.current[key]) {
          frozenOptionsRef.current[key] = currentDynamic[key] || options[key];
        }
        merged[key] = frozenOptionsRef.current[key];
      } else {
        delete frozenOptionsRef.current[key];
        merged[key] = currentDynamic[key] || options[key];
      }
    });

    return merged;
  }, [options, dynamicOptions, activeKeysInstant]);

  const getSectionCount = (keys, filtersToCount) => {
    if (!filtersToCount) return 0;
    return keys.reduce((count, key) => {
      const value = filtersToCount[key];
      if (
        value !== null &&
        value !== undefined &&
        value !== "" &&
        (!Array.isArray(value) || value.length > 0)
      ) {
        return count + 1;
      }
      return count;
    }, 0);
  };

  // Конфигурации тем для секций
  const sectionThemes = {
    locomotive: {
      border: "border-blue-100",
      bgGradient: "from-blue-50",
      iconBg: "bg-[#6766cc]",
      iconText: "text-[#6169ac]",
      titleText: "text-[#6169ac]",
    },
    equipment: {
      border: "border-blue-100",
      bgGradient: "from-blue-50",
      iconBg: "bg-blue-600",
      iconText: "text-blue-700",
      titleText: "text-blue-700",
    },
    repair: {
      border: "border-emerald-100",
      bgGradient: "from-emerald-50",
      iconBg: "bg-emerald-600",
      iconText: "text-emerald-700",
      titleText: "text-emerald-700",
    },
    documents: {
      border: "border-slate-200",
      bgGradient: "from-slate-50",
      iconBg: "bg-slate-600",
      iconText: "text-slate-500",
      titleText: "text-slate-700",
    },
    suppliers: {
      border: "border-violet-100",
      bgGradient: "from-violet-50",
      iconBg: "bg-violet-600",
      iconText: "text-violet-600",
      titleText: "text-violet-800",
    },
    status: {
      border: "border-rose-100",
      bgGradient: "from-rose-50",
      iconBg: "bg-rose-700",
      iconText: "text-rose-600",
      titleText: "text-rose-800",
    },
  };

  return {
    openSections,
    toggleSection,
    updateFilter,
    hasErrors,
    userOptions,
    getSectionCount,
    sectionThemes,
    selectedFields: activeKeysInstant,
    mergedOptions,
    isDynamicLoading,
    isDynamicMode,
  };
};
