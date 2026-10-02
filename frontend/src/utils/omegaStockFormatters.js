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
