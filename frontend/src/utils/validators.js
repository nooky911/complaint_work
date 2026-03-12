import { DATE_MASK, normalizeDateForInput } from "./formatters.js";

export const isValidDate = (dateValue, checkFuture = true) => {
  if (!dateValue || dateValue === DATE_MASK) return true;

  if (dateValue instanceof Date) {
    const isValid = !isNaN(dateValue.getTime());
    if (!isValid) return false;

    if (checkFuture) {
      const now = new Date();
      now.setHours(23, 59, 59, 999);
      return dateValue <= now;
    }
    return true;
  }

  if (typeof dateValue === "string") {
    if (dateValue.trim() === "") return true;
    if (dateValue.includes("_")) return false;

    const normalized = normalizeDateForInput(dateValue);
    if (!/^\d{2}\.\d{2}\.\d{4}$/.test(normalized)) return false;

    const [d, m, y] = normalized.split(".").map(Number);
    if (y < 2000) return false;

    const date = new Date(y, m - 1, d);

    const isCalendarValid =
      date.getFullYear() === y &&
      date.getMonth() === m - 1 &&
      date.getDate() === d;

    if (!isCalendarValid) return false;

    if (checkFuture) {
      const now = new Date();
      now.setHours(23, 59, 59, 999);
      return date <= now;
    }

    return true;
  }

  return false;
};

export const validateFilterDates = (filters, dateFields) => {
  return dateFields.some((field) => {
    const val = filters[field];

    if (!val || val === DATE_MASK) return false;

    if (Array.isArray(val)) {
      if (val.length === 0) return false;
      return val.some((dateItem) => !isValidDate(dateItem, false));
    }

    return !isValidDate(val, false);
  });
};
