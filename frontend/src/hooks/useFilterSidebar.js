import { useState, useEffect, useMemo } from "react";
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

export const useFilterSidebar = (filters, options, appliedFilters = {}) => {
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

  const debouncedAppliedFilters = useDebounce(appliedFilters, 500);

  const hasActiveFilters = useMemo(() => {
    return Object.entries(debouncedAppliedFilters).some(([key, value]) => {
      if (key === "skip" || key === "limit") return false;
      if (Array.isArray(value)) return value.length > 0;
      return (
        value !== "" && value !== null && value !== undefined && value !== 0
      );
    });
  }, [debouncedAppliedFilters]);

  useEffect(() => {
    setIsDynamicMode(hasActiveFilters);
  }, [hasActiveFilters]);

  const { data: dynamicOptionsData, isLoading: isDynamicLoading } =
    useDynamicFilterOptions(isDynamicMode ? debouncedAppliedFilters : {});

  useEffect(() => {
    if (dynamicOptionsData) {
      setDynamicOptions(dynamicOptionsData);
    }
  }, [dynamicOptionsData]);

  useEffect(() => {
    if (!isDynamicMode) {
      setDynamicOptions(null);
    }
  }, [isDynamicMode]);

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

  const selectedFields = useMemo(() => {
    return Object.keys(appliedFilters).filter((key) => {
      const value = appliedFilters[key];
      if (Array.isArray(value)) return value.length > 0;
      return (
        value !== "" && value !== null && value !== undefined && value !== 0
      );
    });
  }, [appliedFilters]);

  const mergedOptions = useMemo(() => {
    if (!isDynamicMode || !dynamicOptions) return options;

    const merged = { ...options };

    const optionsToFiltersMap = {
      models: "locomotive_model",
      series: "locomotive_series",
      statuses: "status",
      suppliers: "supplier",
      equipment_types: "equipment_type",
      regional_centers: "regional_center",
      malfunction_types: "malfunction",
      repair_types: "repair_type",
      equipment_owners: "equipment_owner",
      performed_by: "performed_by",
      destinations: "destination",
      components: "component",
      elements: "element",
      new_components: "new_component",
      new_elements: "new_element",
    };

    Object.keys(dynamicOptions).forEach((key) => {
      const filterKey = optionsToFiltersMap[key] || key;

      if (!selectedFields.includes(filterKey)) {
        merged[key] = dynamicOptions[key];
      }
    });

    return merged;
  }, [isDynamicMode, dynamicOptions, options, selectedFields]);

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
    selectedFields,
    mergedOptions,
    isDynamicLoading,
    isDynamicMode,
  };
};
