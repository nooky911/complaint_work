import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

import api from "../../api/api";
import { buildFilterParams } from "../../utils/filterUtils";

// Хук для получения базовых опций фильтров
export const useFilterOptions = () => {
  return useQuery({
    queryKey: ["filter-options", "static"],
    queryFn: async () => {
      const res = await api.get("/references/filter-options");
      return res.data;
    },
    staleTime: 10 * 60 * 1000, // 10 минут
  });
};

// Хук для динамических опций фильтров
export const useDynamicFilterOptions = (filters) => {
  const memoizedParams = useMemo(() => {
    const params = buildFilterParams(filters, 0, 50);
    params.delete("skip");
    params.delete("limit");
    return params.toString();
  }, [filters]);

  return useQuery({
    queryKey: ["dynamicFilterOptions", memoizedParams],
    queryFn: async () => {
      const res = await api.get(
        `/references/dynamic-filter-options?${memoizedParams}`,
      );
      return res.data;
    },
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
    enabled: memoizedParams.length > 0,
    refetchOnWindowFocus: false,
  });
};

// Хук для получения всех случаев (для абсолютной нумерации)
export const useAllCasesForNumbering = () => {
  return useQuery({
    queryKey: ["cases", "all", "numbering"],
    queryFn: async () => {
      const res = await api.get("/cases/?limit=1000");
      return Array.isArray(res.data) ? res.data : [];
    },
    staleTime: 10 * 60 * 1000, // 10 минут
    enabled: true,
  });
};

// Хук для получения списка случаев
export const useCasesList = (filters, sortOrder) => {
  return useQuery({
    queryKey: ["cases", filters, sortOrder],
    queryFn: async () => {
      const params = buildFilterParams(filters, 0, 50);
      const res = await api.get(`/cases/?${params.toString()}`);
      return Array.isArray(res.data) ? res.data : [];
    },
    staleTime: 2 * 60 * 1000, // 2 минуты
    enabled: true,
  });
};

// Хук для получения деталей случая
export const useCaseDetail = (caseId) => {
  return useQuery({
    queryKey: ["case", caseId],
    queryFn: async () => {
      if (!caseId) return null;
      const res = await api.get(`/cases/${caseId}`);
      return res.data;
    },
    enabled: !!caseId,
    staleTime: 5 * 60 * 1000, // 5 минут
  });
};

// Хук для обновления случая
export const useUpdateCase = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ caseId, data }) => {
      const res = await api.patch(`/cases/${caseId}`, data);
      return res.data;
    },
    onMutate: async ({ caseId, data }) => {
      await queryClient.cancelQueries({ queryKey: ["case", caseId] });
      await queryClient.cancelQueries({ queryKey: ["cases"] });

      const previousCaseData = queryClient.getQueryData(["case", caseId]);

      const previousCasesQueries = queryClient.getQueriesData({
        queryKey: ["cases"],
      });

      const currentCase = queryClient.getQueryData(["case", caseId]);
      const updatedCase = { ...currentCase, ...data };
      queryClient.setQueryData(["case", caseId], updatedCase);

      queryClient.setQueriesData(
        { queryKey: ["cases"] },
        (old) => old?.map((c) => (c.id === caseId ? updatedCase : c)) || [],
      );

      return { previousCaseData, previousCasesQueries };
    },
    onError: (error, variables, context) => {
      // Rollback при ошибке
      if (context?.previousCaseData) {
        queryClient.setQueryData(
          ["case", variables.caseId],
          context.previousCaseData,
        );
      }
      if (context?.previousCasesQueries) {
        context.previousCasesQueries.forEach(([queryKey, queryData]) => {
          queryClient.setQueryData(queryKey, queryData);
        });
      }
      console.error("Ошибка обновления случая:", error);
    },
    onSuccess: (updatedCase) => {
      queryClient.setQueryData(["case", updatedCase.id], updatedCase);

      queryClient.setQueriesData(
        { queryKey: ["cases"] },
        (old) =>
          old?.map((c) => (c.id === updatedCase.id ? updatedCase : c)) || [],
      );
    },
  });
};

// Хук для удаления случая
export const useDeleteCase = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (caseId) => {
      await api.delete(`/cases/${caseId}`);
      return caseId;
    },
    onMutate: async (caseId) => {
      await queryClient.cancelQueries({ queryKey: ["cases"] });
      const previousCases = queryClient.getQueriesData({ queryKey: ["cases"] });

      // Оптимистично удаляем из всех списков
      queryClient.setQueriesData({ queryKey: ["cases"] }, (old) => {
        if (!Array.isArray(old)) return old;
        return old.filter((c) => c.id !== caseId);
      });

      return { previousCases };
    },
    onError: (error, caseId, context) => {
      if (context?.previousCases) {
        context.previousCases.forEach(([key, value]) =>
          queryClient.setQueryData(key, value),
        );
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({
        queryKey: ["cases", "all", "numbering"],
      });
    },
  });
};
