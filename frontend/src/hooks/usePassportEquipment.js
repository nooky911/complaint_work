import { useQuery } from "@tanstack/react-query";
import api from "../api/api";

/** Загружает экземпляры паспорта или состав замены для создания и редактирования случая */
export const usePassportEquipment = (data, preview = false) => {
  // До указания даты акта можно выбрать экземпляры из текущего состава паспорта
  const enabled = !!(data?.passport_id && data?.section_mask);
  const links = (data?.passport_links || []).map(
    ({ node_id, role, parent_node_id, version }) => ({
      node_id,
      role,
      parent_node_id,
      version,
    }),
  );
  const params = {
    component_equipment_id: data?.component_equipment_id || undefined,
    element_equipment_id: data?.element_equipment_id || undefined,
    section_mask: data?.section_mask,
    fault_date: data?.fault_date || undefined,
    case_id: data?.id || undefined,
    component_node_ids: !preview
      ? links
          .filter((x) => x.role === "component")
          .map((x) => x.node_id)
          .join(",") || undefined
      : undefined,
  };
  return useQuery({
    queryKey: [
      "product-passports",
      preview ? "replacement-preview" : "equipment-options",
      data?.passport_id,
      params,
      ...(preview ? [data?.repair_type_id, links] : []),
    ],
    queryFn: async ({ signal }) =>
      preview
        ? (
            await api.post(
              `/product-passports/${data.passport_id}/replacement-preview`,
              {
                ...params,
                element_equipment_id: params.element_equipment_id || null,
                repair_type_id: Number(data.repair_type_id),
                passport_links: links,
              },
              { signal },
            )
          ).data
        : (
            await api.get(
              `/product-passports/${data.passport_id}/equipment-options`,
              { params, signal },
            )
          ).data,
    enabled: enabled && (!preview || !!(links.length && data?.repair_type_id)),
    retry: false,
    staleTime: 0,
  });
};
