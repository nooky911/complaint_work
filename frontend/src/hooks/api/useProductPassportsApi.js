import { useQuery } from "@tanstack/react-query";

import {
  getProductPassport,
  getProductPassportModels,
  searchProductPassports,
} from "../../api/productPassports";

export const useProductPassportModels = () =>
  useQuery({
    queryKey: ["product-passports", "models"],
    queryFn: getProductPassportModels,
    staleTime: 5 * 60 * 1000,
  });

export const useProductPassportSearch = (locomotiveModelId, productNumber) =>
  useQuery({
    queryKey: ["product-passports", "search", locomotiveModelId, productNumber],
    queryFn: () => searchProductPassports(locomotiveModelId, productNumber),
    enabled: Boolean(locomotiveModelId && productNumber.trim()),
    staleTime: 60 * 1000,
  });

export const useProductPassport = (passportId) =>
  useQuery({
    queryKey: ["product-passports", passportId],
    queryFn: () => getProductPassport(passportId),
    enabled: Boolean(passportId),
  });
