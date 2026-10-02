import { useQuery } from "@tanstack/react-query";

import {
  getOmegaStockDocuments,
  getOmegaStockFiles,
  getOmegaStockItems,
} from "../../api/omegaStock";

export const useOmegaStockDocuments = (kind, page, pageSize) =>
  useQuery({
    queryKey: ["omega-stock", "documents", kind, page, pageSize],
    queryFn: () =>
      getOmegaStockDocuments(kind, (page - 1) * pageSize, pageSize + 1),
    enabled: Boolean(kind),
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
