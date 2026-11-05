import { useQuery } from "@tanstack/react-query";

import {
  getProductPassport,
  getProductPassportModels,
  searchProductPassports,
} from "../../api/productPassports";

export const useProductPassportModels = (direction = "loco") =>
  useQuery({
    queryKey: ["product-passports", "models", direction],
    queryFn: () => getProductPassportModels(direction),
    staleTime: 5 * 60 * 1000,
  });

export const useProductPassportSearch = (
  modelId,
  productNumber,
  direction = "loco",
) =>
  useQuery({
    queryKey: [
      "product-passports",
      "search",
      direction,
      modelId,
      productNumber,
    ],
    queryFn: () => searchProductPassports(modelId, productNumber, direction),
    enabled: Boolean(modelId && productNumber.trim()),
    staleTime: 60 * 1000,
  });

export const useProductPassport = (passportId) =>
  useQuery({
    queryKey: ["product-passports", passportId],
    queryFn: () => getProductPassport(passportId),
    enabled: Boolean(passportId),
  });
