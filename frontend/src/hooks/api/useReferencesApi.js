import { useQuery } from "@tanstack/react-query";

import api from "../../api/api";

// Хук для получения справочников для формы
export const useFormReferences = (userRole) => {
  return useQuery({
    queryKey: ["references", "case-form", userRole],
    queryFn: async () => {
      const requests = [
        api.get("/references/case-form"),
        api.get("/references/equipment-all-flat"),
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
