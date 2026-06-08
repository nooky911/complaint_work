import { useMemo } from "react";

import { isValidDate, isDateNotEarlierThan } from "../utils/validators";

const getDepth = (id, equipmentMap) => {
  if (!id || !equipmentMap) return -1;

  const targetId = Number(id);
  let current = equipmentMap.get(targetId);

  if (!current) return -1;

  let calculatedDepth = 0;
  let temp = current;
  let safetyCounter = 0;

  while (temp.parent_id && safetyCounter < 10) {
    const pId = Number(temp.parent_id);
    const parent = equipmentMap.get(pId);

    if (!parent) break;

    temp = parent;
    calculatedDepth++;
    safetyCounter++;
  }

  return calculatedDepth;
};

export const useCaseValidation = (formData, hierarchy, allEquipment = []) => {
  const equipmentMap = useMemo(() => {
    if (!allEquipment || allEquipment.length === 0) return null;
    return new Map(allEquipment.map((item) => [Number(item.id), item]));
  }, [allEquipment]);

  return useMemo(() => {
    const d = formData;
    const w = d?.warranty_work || {};
    const levels = hierarchy?.fullHierarchy || hierarchy || {};
    const rId = Number(d?.repair_type_id || d?.repair_type?.id);

    // Даты
    const isFaultDateMissing = !d?.fault_date;
    const isFaultDateInvalid = d?.fault_date && !isValidDate(d?.fault_date);
    const otherDates = [
      w?.notification_date,
      w?.re_notification_date,
      w?.response_letter_date,
      w?.claim_act_date,
      w?.work_completion_act_date,
    ].filter(Boolean);
    const areOtherDatesInvalid = otherDates.some((date) => !isValidDate(date));

    // Проверка, что даты рекламационной работы не раньше fault_date
    const areOtherDatesEarlierThanFault = otherDates.some(
      (date) => !isDateNotEarlierThan(date, d?.fault_date),
    );

    // TTN даты (можно будущие даты)
    const ttn = d?.waybill_doc || {};
    const ttnDates = [
      ttn?.ttn_replacement_date,
      ttn?.ttn_from_rc_date,
      ttn?.ttn_to_supplier_date,
      ttn?.ttn_from_supplier_date,
    ].filter(Boolean);
    const areTTNDatesInvalid = ttnDates.some(
      (date) => !isValidDate(date, false),
    ); // false = разрешаем будущие даты

    const dateError =
      isFaultDateMissing ||
      isFaultDateInvalid ||
      areOtherDatesInvalid ||
      areOtherDatesEarlierThanFault ||
      areTTNDatesInvalid;

    // Общие обязательные поля
    const isSectionMissing = !d?.section_mask;
    const isRegionMissing = !d?.regional_center_id;
    const isLocoModelMissing = !d?.locomotive_model_id;
    const isDiscoveredAtMissing = !d?.fault_discovered_at_id;
    const isQuantityInvalid =
      !d?.component_quantity || Number(d?.component_quantity) < 1;

    // Неисправное
    const hasLvl1 = !!levels.lvl1;
    const hasLvl2 = !!levels.lvl2;
    const hasLvl3 = !!levels.lvl3;
    const hasLvl4 = !!levels.lvl4;

    const isType1Blocked = rId === 1 && !hasLvl1;
    const isType2Blocked = rId === 2 && !hasLvl2;
    const isType3Blocked = rId === 3 && !hasLvl4;
    const isRepairTypeBlocked =
      isType1Blocked || isType2Blocked || isType3Blocked;

    const isDesignationMissing = rId === 2 || rId === 3 ? !hasLvl3 : !hasLvl1;
    const isMalfunctionMissing = !d?.malfunction_id;

    // Новое оборудование
    const newCompId = d?.new_component_equipment_id;
    const newElemId = d?.new_element_equipment_id;

    const depth = equipmentMap ? getDepth(newCompId, equipmentMap) : 99;

    // Валидация нового оборудования по глубине
    let isNewComponentMissing = false;
    if (equipmentMap) {
      if (rId === 1) isNewComponentMissing = depth < 1;
      else if (rId === 2) isNewComponentMissing = depth < 2;
      else if (rId === 8) isNewComponentMissing = !newCompId;
    }

    const isNewElementMissing = rId === 3 && !newElemId;

    const errors = {
      dateError,
      isFaultDateInvalid,
      areOtherDatesInvalid,
      areOtherDatesEarlierThanFault,
      areTTNDatesInvalid,
      isFaultDateMissing,
      isSectionMissing,
      isRegionMissing,
      isLocoModelMissing,
      isDiscoveredAtMissing,
      isQuantityInvalid,
      isDesignationMissing,
      isMalfunctionMissing,
      isRepairTypeMissing: !rId,
      isRepairTypeBlocked,
      isNewComponentMissing,
      isNewElementMissing,
      blockType: { isType1Blocked, isType2Blocked, isType3Blocked },
    };

    const hasErrors = Object.entries(errors).some(([key, value]) => {
      if (key === "blockType") return false;
      return value === true;
    });

    return { ...errors, hasErrors, isSaveDisabled: hasErrors };
  }, [formData, hierarchy, equipmentMap]);
};
