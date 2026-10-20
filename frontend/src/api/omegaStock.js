import api from "./api";

export const getOmegaStockDocuments = async (
  kind,
  offset = 0,
  limit = 50,
  filters = {},
  sort = null,
) => {
  const response = await api.post(
    `/omega-stock/documents/${kind}/search`,
    { filters },
    {
      params: {
        offset,
        limit,
        ...(sort?.column && {
          sort_column: sort.column,
          sort_direction: sort.direction,
        }),
      },
    },
  );
  return response.data;
};

export const getOmegaStockFilterOptions = async (
  kind,
  column,
  filters = {},
) => {
  const response = await api.post(
    `/omega-stock/documents/${kind}/filter-options/${column}`,
    { filters },
  );
  return response.data;
};

export const getOmegaStockItems = async (kind, documentId) => {
  const response = await api.get(
    `/omega-stock/documents/${kind}/${documentId}/items`,
  );
  return response.data;
};

export const getOmegaStockFiles = async (kind, documentId) => {
  const response = await api.get(
    `/omega-stock/documents/${kind}/${documentId}/files`,
  );
  return response.data;
};

export const omegaStockFileUrl = (kind, documentId, fileId) =>
  `/api/v1/omega-stock/documents/${kind}/${documentId}/files/${fileId}`;

/** Возвращает страницу случаев, доступных для привязки складского документа */
export const getStockLinkCases = async (filters, offset, limit) => {
  const response = await api.post(
    "/omega-stock/link-cases/search",
    { filters },
    { params: { offset, limit } },
  );
  return response.data;
};

/** Возвращает значения фильтра случаев с учётом прав пользователя */
export const getStockLinkCaseFilterOptions = async (column, filters) => {
  const response = await api.post(
    `/omega-stock/link-cases/filter-options/${column}`,
    { filters },
  );
  return response.data;
};

/** Проверяет перенос или сохраняет подтверждённые данные в выбранные случаи */
export const linkStockDocumentToCases = async (
  kind,
  documentId,
  data,
  preview = false,
) => {
  const response = await api.post(
    `/omega-stock/documents/${kind}/${documentId}/link-cases${preview ? "/preview" : ""}`,
    data,
    { timeout: 180000 },
  );
  return response.data;
};
