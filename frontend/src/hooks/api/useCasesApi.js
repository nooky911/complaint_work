import { useAuth } from "../../context/AuthContext";
import { restrictedApi } from "../../features/restricted-view/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

import api from "../../api/api";
import { buildFilterParams } from "../../utils/filterUtils";

// Хук для получения списка номеров случаев
export const useCaseDisplayNumbers = (search, enabled) => {
  const { user } = useAuth();
  return useQuery({
    queryKey: [
      "cases",
      "display-numbers",
      user?.id,
      !!user?.restricted_access,
      search,
    ],
    queryFn: async ({ signal }) => {
      if (user?.restricted_access) return restrictedApi.numbers(search, signal);
      const response = await api.get("/cases/display-numbers", {
        params: { search, limit: 50 },
        signal,
      });
      return response.data;
    },
    enabled,
    staleTime: 0,
    refetchOnWindowFocus: false,
  });
};

// Хук для получения базовых опций фильтров
export const useFilterOptions = (enabled = true) => {
  const { user } = useAuth();
  return useQuery({
    queryKey: ["filter-options", "static", user?.id, !!user?.restricted_access],
    queryFn: async () => {
      if (user?.restricted_access) return restrictedApi.filters();
      const res = await api.get("/references/filter-options");
      return res.data;
    },
    staleTime: 10 * 60 * 1000, // 10 минут
    enabled,
  });
};

// Хук для динамических опций фильтров
export const useDynamicFilterOptions = (filters) => {
  const { user } = useAuth();
  const memoizedParams = useMemo(() => {
    const params = buildFilterParams(filters, 0, 50);
    params.delete("skip");
    params.delete("limit");
    return params.toString();
  }, [filters]);

  return useQuery({
    queryKey: [
      "dynamicFilterOptions",
      user?.id,
      !!user?.restricted_access,
      memoizedParams,
    ],
    queryFn: async () => {
      if (user?.restricted_access) return restrictedApi.filters(filters);
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

// Хук для получения списка случаев
export const useCasesList = (filters, sortOrder, page = 1, limit = 25) => {
  const { user } = useAuth();
  return useQuery({
    queryKey: [
      "cases",
      user?.id,
      !!user?.restricted_access,
      filters,
      sortOrder,
      page,
      limit,
    ],
    queryFn: async () => {
      if (user?.restricted_access)
        return restrictedApi.list(filters, sortOrder, page, limit);
      const skip = (page - 1) * limit;
      const params = buildFilterParams(filters, skip, limit);
      params.append("sort_order", sortOrder);
      const res = await api.get(`/cases/?${params.toString()}`);
      return res.data;
    },
    staleTime: 2 * 60 * 1000,
    enabled: true,
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
  });
};

// Хук для получения деталей случая
export const useCaseDetail = (caseId) => {
  const { user } = useAuth();
  return useQuery({
    queryKey: user?.restricted_access
      ? ["restricted-case", user.id, caseId]
      : ["case", caseId],
    queryFn: async () => {
      if (!caseId) return null;
      if (user?.restricted_access) return restrictedApi.detail(caseId);
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

      queryClient.setQueriesData({ queryKey: ["cases"] }, (old) => {
        if (!old || !Array.isArray(old.items)) return old;
        return {
          ...old,
          items: old.items.map((c) => (c.id === caseId ? updatedCase : c)),
        };
      });

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

      queryClient.setQueriesData({ queryKey: ["cases"] }, (old) => {
        if (!old || !Array.isArray(old.items)) return old;
        return {
          ...old,
          items: old.items.map((c) =>
            c.id === updatedCase.id ? updatedCase : c,
          ),
        };
      });
      queryClient.invalidateQueries({ queryKey: ["case", updatedCase.id] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
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

      queryClient.setQueriesData({ queryKey: ["cases"] }, (old) => {
        if (!old || !Array.isArray(old.items)) return old;
        return {
          ...old,
          items: old.items.filter((c) => c.id !== caseId),
          total: Math.max(0, old.total - 1),
        };
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

// Хук для блокировки случая
export const useLockCase = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (caseId) => {
      const res = await api.post(`/cases/${caseId}/lock`);
      return res.data;
    },
    onSuccess: (updatedCase) => {
      queryClient.setQueryData(["case", updatedCase.id], updatedCase);
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
};

// Хук для снятия блокировки
export const useUnlockCase = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (caseId) => {
      await api.post(`/cases/${caseId}/unlock`);
      return caseId;
    },
    onSuccess: (caseId) => {
      queryClient.invalidateQueries({ queryKey: ["case", caseId] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
};
