// Константы для проверки дат на корректность ввода
export const FILTER_DATE_FIELDS = [
  "date_from",
  "date_to",
  "notification_date",
  "re_notification_date",
  "response_letter_date",
  "claim_act_date",
  "work_completion_act_date",
];

// Изначальное состояние
export const INITIAL_FILTERS = {
  date_from: "",
  date_to: "",
  regional_center_id: [],
  locomotive_model_id: [],
  component_equipment_id: [],
  element_equipment_id: [],
  malfunction_id: [],
  repair_type_id: [],
  supplier_id: [],
  equipment_owner_id: [],
  performed_by_id: [],
  destination_id: [],
  new_component_equipment_id: [],
  new_element_equipment_id: [],
  component_serial_number_new: [],
  element_serial_number_new: [],

  section_mask: 0,
  locomotive_number: [],
  component_serial_number_old: [],
  element_serial_number_old: [],

  status: [],

  notification_number: [],
  re_notification_number: [],
  response_letter_number: [],
  claim_act_number: [],
  work_completion_act_number: [],

  notification_date: "",
  re_notification_date: "",
  response_letter_date: "",
  claim_act_date: "",
  work_completion_act_date: "",

  notification_summary_id: [],
  response_summary_id: [],
  decision_summary_id: [],
  user_id: [],
};

// Наборы ключей для каждого блока FilterSidebar
export const SECTIONS_KEYS = {
  locomotive: [
    "locomotive_model_id",
    "locomotive_number",
    "regional_center_id",
  ],
  equipment: [
    "component_equipment_id",
    "component_serial_number_old",
    "element_equipment_id",
    "element_serial_number_old",
  ],
  repair: [
    "repair_type_id",
    "performed_by_id", 
    "destination_id",
    "equipment_owner_id",
    "new_component_equipment_id",
    "new_element_equipment_id",
    "component_serial_number_new",
    "element_serial_number_new",
  ],
  suppliers: ["supplier_id"],
  status: ["status", "creator_id"],
  documents: [
    "notification_number",
    "notification_date_start",
    "notification_date_end",
    "re_notification_number",
    "response_letter_number",
    "claim_act_number",
    "work_completion_act_number",
  ],
};
