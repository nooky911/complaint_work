import { useMemo } from "react";

import { isValidDate } from "../utils/validators";

const getDepth = (id, allEquipment) => {
  if (!id || !allEquipment || allEquipment.length === 0) return -1;

  const targetId = Number(id);
  let current = allEquipment.find(
    (item) =>
      Number(item.id) === targetId || Number(item.equipment_id) === targetId,
  );

  if (!current) return -1;

  let calculatedDepth = 0;
  let temp = current;
  let safetyCounter = 0;

  while (temp.parent_id && safetyCounter < 10) {
    const pId = Number(temp.parent_id);
    const parent = allEquipment.find(
      (p) => Number(p.id) === pId || Number(p.equipment_id) === pId,
    );

    if (!parent) break;

    temp = parent;
    calculatedDepth++;
    safetyCounter++;
  }

  return calculatedDepth;
};

export const useCaseValidation = (formData, hierarchy, allEquipment = []) => {
  return useMemo(() => {
    const d = formData;
    const w = d?.warranty_work || {};
    const levels = hierarchy?.fullHierarchy || hierarchy || {};
    const rId = Number(d?.repair_type_id || d?.repair_type?.id);

    // 1. ДАТЫ
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
    const dateError =
      isFaultDateMissing || isFaultDateInvalid || areOtherDatesInvalid;

    // 2. ОБЯЗАТЕЛЬНЫЕ ПОЛЯ (ОБЩЕЕ)
    const isSectionMissing = !d?.section_mask;
    const isRegionMissing = !d?.regional_center_id;
    const isLocoModelMissing = !d?.locomotive_model_id;
    const isDiscoveredAtMissing = !d?.fault_discovered_at_id;
    const isQuantityInvalid =
      !d?.component_quantity || Number(d?.component_quantity) < 1;

    // 3. НЕИСПРАВНОЕ
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

    // 4. ИСПОЛНЕНИЕ
    const newCompId = d?.new_component_equipment_id;
    const newElemId = d?.new_element_equipment_id;

    const isEquipLoaded = allEquipment && allEquipment.length > 0;
    const depth = isEquipLoaded ? getDepth(newCompId, allEquipment) : 99;

    // Валидация нового оборудования по глубине
    let isNewComponentMissing = false;
    if (isEquipLoaded) {
      if (rId === 1) isNewComponentMissing = depth < 1;
      else if (rId === 2) isNewComponentMissing = depth < 2;
      else if (rId === 8) isNewComponentMissing = !newCompId;
    }

    const isNewElementMissing = rId === 3 && !newElemId;

    const errors = {
      dateError,
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
  }, [formData, hierarchy, allEquipment]);
};
