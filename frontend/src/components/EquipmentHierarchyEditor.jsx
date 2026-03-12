import React, { useMemo } from "react";

import { useEquipmentHierarchy } from "../hooks/useEquipmentHierarchy";
import {
  EquipmentLevelSelector,
  EquipmentFields,
  EquipmentMalfunctionSelector,
} from "./equipment";

export const EquipmentHierarchyEditor = ({
  isEditing,
  currentId,
  onSelect,
  currentData,
  updateField,
  references,
  allEquipment = [],
  mode = "old",
  initialLevels = null,
  filterStrategy = "NONE",
  errorElement,
  errorDesignation,
  errorMalfunction,
}) => {
  const {
    levels,
    labels,
    equipmentWithLevels,
    activeId,
    handleLevelSelect,
    getFilteredOptions,
    getVisibleIndices,
  } = useEquipmentHierarchy({
    currentId,
    allEquipment,
    mode,
    initialLevels,
    currentData,
    updateField,
    isEditing,
  });

  const visibleIndices = useMemo(
    () => getVisibleIndices(filterStrategy),
    [filterStrategy, getVisibleIndices],
  );

  if (!isEditing || (mode === "new" && visibleIndices.length === 0))
    return null;

  return (
    <div
      className={
        mode === "old"
          ? "space-y-3 rounded-2xl border border-slate-200 bg-slate-200/50 p-3 shadow-sm"
          : "space-y-0"
      }
    >
      <div className="grid grid-cols-1 gap-3">
        {visibleIndices.map((i) => (
          <EquipmentLevelSelector
            key={i}
            index={i}
            label={mode === "new" && i === 3 ? "Компонент" : labels[i]}
            value={levels[`lvl${i}`]}
            options={getFilteredOptions(i)}
            isDisabled={equipmentWithLevels.length === 0}
            onChange={(id) => handleLevelSelect(i, id, onSelect)}
            error={i === 3 ? errorDesignation : i === 4 ? errorElement : false}
          />
        ))}
      </div>

      {mode === "old" && (
        <>
          <EquipmentFields
            mode={mode}
            levels={levels}
            currentData={currentData}
            updateField={updateField}
            isEditing={isEditing}
          />
          <EquipmentMalfunctionSelector
            activeId={activeId}
            currentData={currentData}
            updateField={updateField}
            references={references}
            errorMalfunction={errorMalfunction}
          />
        </>
      )}

      {mode === "new" && (
        <div className="mt-2 space-y-3">
          <EquipmentFields
            mode={mode}
            levels={levels}
            currentData={currentData}
            updateField={updateField}
            isEditing={isEditing}
          />
        </div>
      )}
    </div>
  );
};
