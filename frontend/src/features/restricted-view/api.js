import api from "../../api/api";

const relations = [
  "regional_center",
  "locomotive_model",
  "component_equipment",
  "element_equipment",
  "malfunction",
  "fault_discovered_at",
  "repair_type",
  "performed_by",
  "equipment_owner",
  "destination",
  "new_component_equipment",
  "new_element_equipment",
  "supplier",
];
const summaries = [
  "notification_summary",
  "response_summary",
  "decision_summary",
  "research_status",
  "investigation_reason",
];
const warranty = [
  "notification_number",
  "notification_date",
  "re_notification_number",
  "re_notification_date",
  "response_letter_number",
  "response_letter_date",
  "claim_act_number",
  "claim_act_date",
  "work_completion_act_number",
  "work_completion_act_date",
  "research_document",
];
const optionFields = {
  regional_centers: "regional_center",
  locomotive_models: "locomotive_model",
  components: "component_equipment",
  elements: "element_equipment",
  malfunctions: "malfunction",
  repair_types: "repair_type",
  performed_by: "performed_by",
  equipment_owners: "equipment_owner",
  destinations: "destination",
  new_components: "new_component_equipment",
  new_elements: "new_element_equipment",
  notification_summaries: "notification_summary",
  response_summaries: "response_summary",
  decision_summaries: "decision_summary",
  research_statuses: "research_status",
  investigation_reasons: "investigation_reason",
};
const scalarOptions = {
  locomotive_numbers: "locomotive_number",
  component_serial_numbers: "component_serial_number_old",
  element_serial_numbers: "element_serial_number_old",
  component_serial_numbers_new: "component_serial_number_new",
  element_serial_numbers_new: "element_serial_number_new",
  notification_numbers: "notification_number",
  notification_dates: "notification_date",
  re_notification_numbers: "re_notification_number",
  re_notification_dates: "re_notification_date",
  response_letter_numbers: "response_letter_number",
  response_letter_dates: "response_letter_date",
  claim_act_numbers: "claim_act_number",
  claim_act_dates: "claim_act_date",
  work_completion_act_numbers: "work_completion_act_number",
  work_completion_act_dates: "work_completion_act_date",
  research_documents: "research_document",
};

/** Приводит разрешённые поля к форме существующих карточек без подстановки скрытых данных */
function adaptCase(row) {
  const result = { ...row, warranty_work: {} };
  for (const key of relations)
    result[key] =
      row[key] == null ? null : { id: row[`${key}_id`], name: row[key] };
  for (const key of warranty) result.warranty_work[key] = row[key];
  for (const key of summaries)
    result.warranty_work[key] =
      row[key] == null ? null : { id: row[`${key}_id`], name: row[key] };
  return result;
}

/** Использует отдельные защищённые запросы для общего Dashboard и карточки */
export const restrictedApi = {
  list: async (filters, sortOrder, page, size) => {
    const { data } = await api.get("/restricted/cases", {
      params: {
        filters: JSON.stringify(filters),
        sort_order: sortOrder,
        page,
        size,
      },
    });
    return { ...data, items: data.items.map(adaptCase) };
  },
  detail: async (id) =>
    adaptCase((await api.get(`/restricted/cases/${id}`)).data),
  numbers: async (search, signal) =>
    (
      await api.get("/restricted/cases/display-numbers", {
        params: { search },
        signal,
      })
    ).data,
  filters: async (filters = {}) => {
    const { data } = await api.get("/restricted/cases/filters", {
      params: { filters: JSON.stringify(filters) },
    });
    const result = {};
    for (const [option, key] of Object.entries(optionFields))
      result[option] = data.references[key] || [];
    for (const [option, key] of Object.entries(scalarOptions))
      result[option] = (data.options[key] || [])
        .filter((v) => v !== null && v !== "")
        .map((v) => ({ id: v, name: String(v) }));
    return result;
  },
};
