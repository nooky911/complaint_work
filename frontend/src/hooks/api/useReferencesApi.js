import { useQuery } from "@tanstack/react-query";

import api from "../../api/api";

export const useLocomotiveNumbers = (modelId, search = "", enabled = true) =>
  useQuery({
    queryKey: ["references", "locomotive-numbers", modelId, search],
    queryFn: async ({ signal }) => {
      const response = await api.get("/references/locomotive-numbers", {
        params: { locomotive_model_id: modelId, search, limit: 200 },
        signal,
      });
      return response.data;
    },
    enabled: enabled && !!modelId,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

// Хук для получения справочников для формы
export const useFormReferences = (userRole) => {
  return useQuery({
    queryKey: ["references", "case-form", userRole],
    queryFn: async () => {
      const requests = [
        api.get("/references/case-form"),
        api.get("/equipment/equipment-all-flat"),
      ];

      if (userRole === "superadmin") {
        requests.push(api.get("/users/"));
      }

      const responses = await Promise.all(requests);

      if (userRole === "superadmin") {
        return {
          references: responses[0].data,
          equipment: responses[1].data,
          users: responses[2].data,
        };
      }

      return {
        references: responses[0].data,
        equipment: responses[1].data,
        users: null,
      };
    },
    staleTime: 30 * 60 * 1000, // 30 минут
    enabled: !!userRole,
  });
};
