import React, { useMemo, useEffect, useCallback } from "react";

import { SelectField } from "./inputs/index";
import { EquipmentHierarchyEditor } from "./EquipmentHierarchyEditor";
import { REPAIR_FIELDS_LABELS } from "../constants/labels";

export const RepairExecutionEditor = ({
  isEditing,
  currentData,
  updateField,
  references,
  allEquipment,
  faultyHierarchy,
  showError,
  validation,
}) => {
  const rId = Number(
    currentData?.repair_type?.id || currentData?.repair_type_id,
  );

  const hasLevel3 = Boolean(faultyHierarchy?.fullHierarchy?.lvl3);
  const isRepairTypeDisabled = !hasLevel3;

  // ЕДИНАЯ ФУНКЦИЯ ОЧИСТКИ ВСЕХ ЗАВИСИМЫХ ПОЛЕЙ
  const resetAllRepairFields = useCallback(() => {
    const fieldsToReset = [
      "new_component_equipment_id",
      "new_component_quantity",
      "new_element_equipment_id",
      "new_element_quantity",
      "performed_by_id",
      "equipment_owner_id",
      "destination_id",
    ];

    const stringFieldsToReset = [
      "component_serial_number_new",
      "component_manufacture_date_new",
      "element_serial_number_new",
      "element_manufacture_date_new",
    ];

    fieldsToReset.forEach((field) => updateField(field, null));
    stringFieldsToReset.forEach((field) => updateField(field, ""));
  }, [updateField]);

  // АВТОМАТИЧЕСКИЙ СБРОС
  useEffect(() => {
    if (rId !== 0 && isRepairTypeDisabled && isEditing) {
      updateField("repair_type_id", null);
      resetAllRepairFields();
    }
  }, [isRepairTypeDisabled, rId, isEditing, updateField, resetAllRepairFields]);

  const disabledStyles =
    "border-slate-200 text-slate-400 shadow-none pointer-events-none opacity-70";

  const repairTypePlaceholder = isRepairTypeDisabled
    ? "Выберите неисправное оборудование"
    : "Выберите тип ремонта";

  // Логика доступности полей в зависимости от типа ремонта
  const canEditExecutor = [1, 2, 3, 4, 5, 8].includes(rId);
  const canEditOwner = [1, 2, 3, 5, 8].includes(rId);
  const canEditDestination = [1, 2, 3, 8].includes(rId);

  const strategy = useMemo(() => {
    if (rId === 1) return "LEVEL_1";

    if (rId === 8) {
      return faultyHierarchy?.fullHierarchy?.lvl4 ? "LEVEL_4" : "LEVEL_3";
    }

    if (rId === 2) return "LEVEL_3";
    if (rId === 3) return "LEVEL_4";
    return "NONE";
  }, [rId, faultyHierarchy]);

  // РУЧНОЙ СБРОС
  const handleRepairTypeChange = (val) => {
    const nextId = Number(val);
    if (nextId === rId) return;

    updateField("repair_type_id", nextId);
    resetAllRepairFields();

    const h = faultyHierarchy?.fullHierarchy || {};

    // АВТОПОДСТАНОВКА
    if (h) {
      if (nextId === 2 || (nextId === 8 && !h.lvl4)) {
        updateField("new_component_equipment_id", h.lvl3 || h.lvl2 || h.lvl1);
        updateField("new_component_quantity", 1);
      } else if (nextId === 3 || (nextId === 8 && h.lvl4)) {
        updateField("new_component_equipment_id", h.lvl3 || h.lvl2 || h.lvl1);
        updateField("new_component_quantity", 1);
        updateField("new_element_equipment_id", h.lvl4 || null);
        updateField("new_element_quantity", 1);
      } else if (nextId === 1) {
        updateField("new_component_equipment_id", h.lvl1 || h.lvl0);
        updateField("new_component_quantity", 1);
      }
    }
  };

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-3">
        <SelectField
          label={REPAIR_FIELDS_LABELS.repair_type}
          value={rId}
          options={references?.repair_types}
          isEditing={true}
          onChange={handleRepairTypeChange}
          disabled={isRepairTypeDisabled}
          placeholder={repairTypePlaceholder}
          className={isRepairTypeDisabled ? disabledStyles : ""}
          error={
            showError &&
            (validation.isRepairTypeMissing || validation.isRepairTypeBlocked)
          }
        />

        <SelectField
          label={REPAIR_FIELDS_LABELS.performed_by}
          value={currentData?.performed_by_id}
          options={references?.performed_by}
          isEditing={true}
          disabled={!canEditExecutor}
          className={!canEditExecutor ? disabledStyles : ""}
          placeholder={"—"}
          onChange={(val) => updateField("performed_by_id", val)}
        />
      </div>

      {strategy !== "NONE" && (
        <EquipmentHierarchyEditor
          isEditing={isEditing}
          mode="new"
          currentId={
            strategy === "LEVEL_4"
              ? currentData?.new_element_equipment_id || null
              : currentData?.new_component_equipment_id || null
          }
          allEquipment={allEquipment}
          references={references}
          currentData={currentData}
          updateField={updateField}
          filterStrategy={strategy}
          initialLevels={faultyHierarchy?.fullHierarchy}
          onSelect={(data) => {
            if (data.component) {
              updateField("new_component_equipment_id", data.component);
            }
            updateField("new_element_equipment_id", data.element || null);
          }}
          showError={showError}
          errorDesignation={showError && validation.isNewComponentMissing}
          errorElement={showError && validation.isNewElementMissing}
        />
      )}

      <div className="grid grid-cols-2 gap-3">
        <SelectField
          label={REPAIR_FIELDS_LABELS.equipment_owner}
          value={currentData?.equipment_owner_id}
          options={references?.equipment_owners}
          isEditing={true}
          disabled={!canEditOwner}
          className={!canEditOwner ? disabledStyles : ""}
          placeholder={"—"}
          onChange={(val) => updateField("equipment_owner_id", val)}
        />
        <SelectField
          label={REPAIR_FIELDS_LABELS.destination}
          value={currentData?.destination_id}
          options={references?.destinations}
          isEditing={true}
          disabled={!canEditDestination}
          className={!canEditDestination ? disabledStyles : ""}
          placeholder={"—"}
          onChange={(val) => updateField("destination_id", val)}
        />
      </div>
    </div>
  );
};
