import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/api';

// Мутация для создания поставщика
export const useCreateSupplier = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (name) => {
      const response = await api.post("/equipment/suppliers", {
        supplier_name: name,
      });
      return { name, response };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["management-references"],
      });
    },
  });
};

// Мутация для обновления поставщика
export const useUpdateSupplier = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, name }) => {
      const response = await api.patch(`/equipment/suppliers/${id}`, {
        supplier_name: name,
      });
      return { id, name, response };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["management-references"],
      });
      queryClient.invalidateQueries({ queryKey: ["equipment-flat"] });
    },
  });
};

// Мутация для создания оборудования
export const useCreateEquipment = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ name, parentId }) => {
      const response = await api.post("/equipment", {
        equipment_name: name,
        parent_id: parentId,
      });
      return { name, response };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["equipment-flat"] });
    },
  });
};

// Мутация для обновления оборудования
export const useUpdateEquipment = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, name, supplier_id }) => {
      const payload = {};
      if (name !== undefined) payload.equipment_name = name;
      if (supplier_id !== undefined) payload.supplier_id = supplier_id;
      
      const response = await api.patch(`/equipment/${id}`, payload);
      return { id, name, supplier_id, response };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["equipment-flat"] });
    },
  });
};

// Мутация для обновления неисправности
export const useUpdateMalfunction = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, name }) => {
      const response = await api.patch(`/equipment/malfunctions/${id}`, {
        defect_name: name,
      });
      return { id, name, response };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["management-references"],
      });
    },
  });
};

// Мутация для привязки неисправностей к оборудованию
export const useAttachMalfunctions = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ equipmentId, payload }) => {
      const response = await api.post(`/equipment/${equipmentId}/malfunctions`, payload);
      return { equipmentId, payload, response };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["equipment-flat"] });
      queryClient.invalidateQueries({ queryKey: ["management-references"] });
    },
  });
};
