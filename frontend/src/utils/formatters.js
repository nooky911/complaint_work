import { format } from "date-fns";

import { SECTIONS_CONFIG } from "../constants/sections_mask";

export const DATE_MASK = "__.__.____";

export const formatSectionMask = (mask) => {
  if (!mask || typeof mask !== "number") return "—";

  const active = SECTIONS_CONFIG.filter((s) => mask & s.bit).map(
    (s) => s.label,
  );

  return active.length > 0 ? active.join(", ") : "—";
};

export const formatDate = (dateStr) => {
  if (!dateStr || dateStr === "—" || dateStr === DATE_MASK) return "—";

  if (/^\d{2}\.\d{2}\.\d{4}$/.test(dateStr)) return dateStr;

  try {
    const pureDate = dateStr.includes("T") ? dateStr.split("T")[0] : dateStr;
    if (pureDate.includes("-")) {
      const [year, month, day] = pureDate.split("-");
      return `${day}.${month}.${year}`;
    }
    return dateStr;
  } catch (e) {
    return dateStr;
  }
};

export const normalizeDateForInput = (val) => {
  if (!val || val === "—") return DATE_MASK;

  // Если пришло из БД ГГГГ-ММ-ДД
  if (val.includes("-") && val.length === 10) {
    const [y, m, d] = val.split("-");
    return `${d}.${m}.${y}`;
  }
  return val;
};

export const formatToDB = (dateStr) => {
  if (!dateStr || dateStr === DATE_MASK || dateStr === "—") return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;

  const parts = dateStr.split(".");
  if (parts.length === 3) {
    const [d, m, y] = parts;
    if (d && m && y && d.length === 2 && m.length === 2 && y.length === 4) {
      return `${y}-${m}-${d}`;
    }
  }
  return null;
};

export const getText = (field) => {
  if (!field) return "—";
  let rawText =
    typeof field === "object"
      ? field.name ||
        field.equipment_name ||
        field.locomotive_model_name ||
        field.regional_center_name ||
        "—"
      : field;

  if (typeof rawText === "string") {
    return rawText.replace(/_/g, " ");
  }
  return rawText;
};

// Форматирование имени пользователя -> (Иванов И.И.)
export const formatFullName = (fullName) => {
  const nameStr = typeof fullName === "object" ? fullName?.name : fullName;

  if (!nameStr || nameStr === "Система" || nameStr === "Не указано")
    return "Система";

  const parts = nameStr.split(" ").filter((p) => p.length > 0);

  // Если хотя бы есть Фамилия и Имя
  if (parts.length >= 2) {
    const lastName = parts[0];
    const firstNameChar = parts[1][0] ? `${parts[1][0]}.` : "";
    const middleNameChar = parts[2] && parts[2][0] ? `${parts[2][0]}.` : "";

    return `${lastName} ${firstNameChar}${middleNameChar}`;
  }

  return parts[0];
};

// Конвертация данных случая в форму редактирования
export const convertCaseToFormData = (caseData) => {
  if (!caseData) return null;

  return {
    // Основные поля
    fault_date: caseData.fault_date,
    section_mask: caseData.section_mask,
    locomotive_number: caseData.locomotive_number,
    mileage: caseData.mileage,
    supplier: caseData.supplier || null,

    // Количества
    component_quantity: caseData.component_quantity,
    element_quantity: caseData.element_quantity,
    new_component_quantity: caseData.new_component_quantity,
    new_element_quantity: caseData.new_element_quantity,

    // Серийные номера и даты
    component_serial_number_old: caseData.component_serial_number_old,
    component_manufacture_date_old: caseData.component_manufacture_date_old,
    element_serial_number_old: caseData.element_serial_number_old,
    element_manufacture_date_old: caseData.element_manufacture_date_old,
    component_serial_number_new: caseData.component_serial_number_new || "",
    component_manufacture_date_new:
      caseData.component_manufacture_date_new || "",
    element_serial_number_new: caseData.element_serial_number_new || "",
    element_manufacture_date_new: caseData.element_manufacture_date_new || "",

    // ID полей
    regional_center_id: caseData.regional_center?.id,
    locomotive_model_id: caseData.locomotive_model?.id,
    fault_discovered_at_id: caseData.fault_discovered_at?.id,
    malfunction_id: caseData.malfunction?.id,
    repair_type_id: caseData.repair_type?.id,
    performed_by_id: caseData.performed_by?.id,
    equipment_owner_id: caseData.equipment_owner?.id,
    destination_id: caseData.destination?.id,
    supplier_id: caseData.supplier?.id || null,

    // Оборудование
    component_equipment_id: caseData.component_equipment?.id || null,
    element_equipment_id: caseData.element_equipment?.id || null,
    new_component_equipment_id: caseData.new_component_equipment?.id || "",
    new_element_equipment_id: caseData.new_element_equipment?.id || "",

    // Примечание
    notes: caseData.notes,

    // Владелец случая
    user_id: caseData.user_id,

    // Warranty work
    warranty_work: caseData.warranty_work
      ? {
          notification_number: caseData.warranty_work.notification_number,
          notification_date: caseData.warranty_work.notification_date,
          notification_summary_id:
            caseData.warranty_work.notification_summary?.id,
          re_notification_number: caseData.warranty_work.re_notification_number,
          re_notification_date: caseData.warranty_work.re_notification_date,
          response_letter_number: caseData.warranty_work.response_letter_number,
          response_letter_date: caseData.warranty_work.response_letter_date,
          response_summary_id: caseData.warranty_work.response_summary?.id,
          claim_act_number: caseData.warranty_work.claim_act_number,
          claim_act_date: caseData.warranty_work.claim_act_date,
          work_completion_act_number:
            caseData.warranty_work.work_completion_act_number,
          work_completion_act_date:
            caseData.warranty_work.work_completion_act_date,
          decision_summary_id: caseData.warranty_work.decision_summary?.id,
        }
      : null,
  };
};

export const getInitialCaseData = () => ({
  // 1. Основные поля
  fault_date: format(new Date(), "yyyy-MM-dd"),
  section_mask: null,
  locomotive_number: "",
  mileage: null,

  // 2. Количества
  component_quantity: 1,
  element_quantity: null,
  new_component_quantity: null,
  new_element_quantity: null,

  // 3. Старое оборудование
  component_serial_number_old: "",
  component_manufacture_date_old: null,
  element_serial_number_old: "",
  element_manufacture_date_old: null,

  // 4. ID связей (для Select-ов)
  regional_center_id: null,
  locomotive_model_id: null,
  fault_discovered_at_id: null,
  malfunction_id: null,
  repair_type_id: null,
  performed_by_id: null,
  equipment_owner_id: null,
  destination_id: null,
  supplier_id: null,

  // 5. Оборудование (ID)
  component_equipment_id: null,
  element_equipment_id: null,
  new_component_equipment_id: null,
  new_element_equipment_id: null,

  // 6. Новое оборудование (для блоков замены)
  component_serial_number_new: "",
  component_manufacture_date_new: null,
  element_serial_number_new: "",
  element_manufacture_date_new: null,

  notes: "",

  // 7. Гарантийка
  warranty_work: {
    notification_number: "",
    notification_date: null,
    notification_summary_id: null,
    re_notification_number: "",
    re_notification_date: null,
    response_letter_number: "",
    response_letter_date: null,
    response_summary_id: null,
    claim_act_number: "",
    claim_act_date: null,
    work_completion_act_number: "",
    work_completion_act_date: null,
    decision_summary_id: null,
  },
});

export const formatEquipmentName = (name, quantity) => {
  if (!name) return "—";
  const cleanName = name.replace(/_/g, " ");
  if (quantity && quantity > 1) {
    return `${cleanName} (${quantity} шт.)`;
  }
  return cleanName;
};
