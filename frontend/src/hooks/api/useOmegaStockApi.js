import { useQuery } from "@tanstack/react-query";

import {
  getOmegaStockDocuments,
  getOmegaStockFilterOptions,
  getOmegaStockFiles,
  getOmegaStockItems,
} from "../../api/omegaStock";

export const useOmegaStockDocuments = (kind, page, pageSize, filters, sort) =>
  useQuery({
    queryKey: ["omega-stock", "documents", kind, page, pageSize, filters, sort],
    queryFn: () =>
      getOmegaStockDocuments(kind, (page - 1) * pageSize, pageSize + 1, filters, sort),
    enabled: Boolean(kind),
  });

export const useOmegaStockFilterOptions = (kind, column, filters, enabled) =>
  useQuery({
    queryKey: ["omega-stock", "filter-options", kind, column, filters],
    queryFn: () => getOmegaStockFilterOptions(kind, column, filters),
    enabled: Boolean(kind && column && enabled),
    staleTime: 0,
  });

export const useOmegaStockItems = (kind, documentId) =>
  useQuery({
    queryKey: ["omega-stock", "items", kind, documentId],
    queryFn: () => getOmegaStockItems(kind, documentId),
    enabled: Boolean(kind && documentId),
  });

export const useOmegaStockFiles = (kind, documentId) =>
  useQuery({
    queryKey: ["omega-stock", "files", kind, documentId],
    queryFn: () => getOmegaStockFiles(kind, documentId),
    enabled: Boolean(kind && documentId),
  });
