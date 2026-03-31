import { useQuery } from "@tanstack/react-query";
import api from "../api/api";

export const useEquipmentData = () => {
  const { data: allEquipment, isLoading: equipmentLoading } = useQuery({
    queryKey: ["equipment-flat"],
    queryFn: async () => {
      const response = await api.get("/equipment/equipment-all-flat");
      return response.data;
    },
  });

  const { data: references, isLoading: referencesLoading } = useQuery({
    queryKey: ["management-references"],
    queryFn: async () => {
      const response = await api.get("/references/management-references");
      return response.data;
    },
  });

  const loading = equipmentLoading || referencesLoading;

  const allMalfunctions = references?.malfunctions || [];
  const allSuppliers = references?.suppliers || [];
  const equipmentMalfunctions = references?.equipment_malfunctions || [];

  return {
    allEquipment: allEquipment || [],
    references,
    allMalfunctions,
    allSuppliers,
    equipmentMalfunctions,
    loading,
    equipmentLoading,
    referencesLoading,
  };
};
