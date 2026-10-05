import api from "./api";

export const getOmegaStockDocuments = async (kind, offset = 0, limit = 50, filters = {}) => {
  const response = await api.post(`/omega-stock/documents/${kind}/search`, { filters }, {
    params: { offset, limit },
  });
  return response.data;
};

export const getOmegaStockFilterOptions = async (kind, column, filters = {}) => {
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
