import api from "./api";
import { message } from "antd";

// Экспорт случаев в Excel
export const exportCasesToExcel = async (filters = {}) => {
  try {
    const queryParams = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (
        value === null ||
        value === undefined ||
        value === "" ||
        value === 0
      ) {
        return;
      }

      if (Array.isArray(value)) {
        value.forEach((v) => {
          if (v !== null && v !== undefined && v !== "" && v !== 0) {
            queryParams.append(key, v.toString());
          }
        });
      } else {
        queryParams.append(key, value.toString());
      }
    });

    const response = await api.get(
      `/cases/export${queryParams.toString() ? "?" + queryParams : ""}`,
      {
        responseType: "blob",
      },
    );

    // Получаем имя файла из заголовков
    const contentDisposition = response.headers["content-disposition"];
    let filename = "export.xlsx";
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename\*=utf-8''(.+)/);
      if (filenameMatch) {
        filename = decodeURIComponent(filenameMatch[1]);
      }
    }

    // Создаем blob и скачиваем файл
    const blob = new Blob([response.data], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    return { success: true, filename };
  } catch (error) {
    if (error.response?.status === 404) {
      message.error(
        "По вашим фильтрам ничего не найдено, нечего экспортировать",
      );
      throw new Error("Нет данных для экспорта");
    }

    // Показываем общую ошибку
    const errorMessage =
      error.response?.data?.detail || error.message || "Ошибка экспорта";
    message.error(`Ошибка экспорта: ${errorMessage}`);
    throw error;
  }
};
