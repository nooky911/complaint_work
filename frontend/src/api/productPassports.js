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
