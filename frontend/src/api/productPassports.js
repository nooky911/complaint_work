import api from "./api";

export const getProductPassportModels = async () => {
  const response = await api.get("/product-passports/models");
  return response.data;
};

export const searchProductPassports = async (
  locomotiveModelId,
  productNumber,
) => {
  const response = await api.get("/product-passports/search", {
    params: {
      locomotive_model_id: locomotiveModelId,
      product_number: productNumber,
    },
  });
  return response.data;
};

export const getProductPassport = async (passportId) => {
  const response = await api.get(`/product-passports/${passportId}`);
  return response.data;
};

export const exportProductPassport = async (passportId) => {
  const response = await api.get(`/product-passports/${passportId}/export`, {
    responseType: "blob",
  });
  const disposition = response.headers["content-disposition"];
  const match = disposition?.match(/filename\*=utf-8''([^;]+)/i);
  const filename = match
    ? decodeURIComponent(match[1])
    : `Паспорт_${passportId}.xlsx`;
  const url = window.URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  try {
    link.click();
  } finally {
    link.remove();
    window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
  }
};
