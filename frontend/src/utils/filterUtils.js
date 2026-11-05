import { EMPTY_FILTER_VALUE, INITIAL_FILTERS } from "../constants/filters";

/** Восстанавливает известные фильтры, сохраняя значения по умолчанию при ошибке */
export const readSavedFilters = (storageKey) => {
  let saved;
  try {
    saved = JSON.parse(localStorage.getItem(storageKey));
  } catch {
    saved = null;
  }
  const source =
    saved && typeof saved === "object" && !Array.isArray(saved) ? saved : {};
  return Object.fromEntries(
    Object.entries(INITIAL_FILTERS).map(([key, initial]) => {
      const value = source[key];
      if (Array.isArray(initial)) {
        return [
          key,
          Array.isArray(value)
            ? value.filter(
                (item) =>
                  typeof item === "string" ||
                  (typeof item === "number" && Number.isFinite(item)),
              )
            : [],
        ];
      }
      if (typeof initial === "number") {
        return [
          key,
          Number.isSafeInteger(value) && value >= 0 ? value : initial,
        ];
      }
      return [key, typeof value === "string" ? value : initial];
    }),
  );
};

// Подсчет количества активных фильтров для бейджика
export const countActiveFilters = (filters) => {
  return Object.entries(filters).reduce((acc, [key, val]) => {
    if (key === "skip" || key === "limit") return acc;
    // Массивы
    if (Array.isArray(val)) return acc + val.length;
    // Битовая маска секций
    if (key === "section_mask") return val !== 0 ? acc + 1 : acc;
    // Одиночные значения (строки, даты)
    return val !== "" && val !== null && val !== undefined ? acc + 1 : acc;
  }, 0);
};

// Преобразование объекта фильтров в URLSearchParams
export const buildFilterParams = (filters, skip = 0, limit = 50) => {
  const params = new URLSearchParams();

  params.append("skip", String(skip));
  params.append("limit", String(limit));

  Object.entries(filters).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      if (value.length > 0) {
        value.forEach((v) => {
          if (v === EMPTY_FILTER_VALUE) {
            params.append("empty_fields", key);
          } else if (v !== null && v !== undefined && v !== "") {
            params.append(key, String(v));
          }
        });
      }
    } else if (
      value !== "" &&
      value !== null &&
      value !== undefined &&
      value !== 0
    ) {
      params.append(key, String(value));
    }
  });

  return params;
};
