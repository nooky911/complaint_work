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
          if (v !== null && v !== undefined && v !== "") {
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
