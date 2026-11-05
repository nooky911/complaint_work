import { formatDate } from "./formatters";

export const formatOmegaStockValue = (value, format) => {
  if (format === "files") return value ? "Есть" : "—";
  if (value === null || value === undefined || value === "") return "—";
  if (format === "date") return formatDate(value);
  if (format === "datetime") {
    const date = formatDate(value);
    const time = String(value).split("T")[1]?.slice(0, 5);
    return time ? `${date} ${time}` : date;
  }
  return String(value);
};

/** Определяет раздел склада по переходу, при прямом входе использует раздел пользователя */
export const getStockDirection = (location, user) => {
  if (location.state?.returnTo === "/train") return "train";
  if (location.state?.returnTo === "/dashboard") return "loco";
  return user?.direction === "train" ? "train" : "loco";
};

/** Разрешает привязку из собственного раздела, администратору из любого */
export const canLinkStockCases = (user, direction) =>
  user?.role === "superadmin" ||
  (user?.role === "editor" && user.direction === direction);
