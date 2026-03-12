import { useMemo } from "react";

export const useSearchFilter = (options, searchTerm) => {
  return useMemo(() => {
    if (!options) return [];
    if (!searchTerm) return options;
    const lowerTerm = searchTerm.toLowerCase();
    return options.filter((opt) => {
      const labelText = typeof opt === "object" ? opt.name : String(opt);
      return labelText.toLowerCase().includes(lowerTerm);
    });
  }, [options, searchTerm]);
};
