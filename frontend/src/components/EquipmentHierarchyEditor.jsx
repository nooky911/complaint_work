import React, { useMemo } from "react";

import { useEquipmentHierarchy } from "../hooks/useEquipmentHierarchy";
import { usePassportEquipment } from "../hooks/usePassportEquipment";
import {
  EquipmentLevelSelector,
  EquipmentFields,
  EquipmentMalfunctionSelector,
} from "./equipment";

/** Выбор оборудования с учётом классификатора и состава выбранных секций */
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
  const passportQuery = usePassportEquipment(
    mode === "old" ? currentData : null,
  );
  const passportScope = mode === "old" && !!currentData?.passport_id;
  const classifierLoading =
    passportScope &&
    (!currentData?.section_mask ||
      !passportQuery.data ||
      passportQuery.isError);
  const allowedIds = useMemo(() => {
    if (!passportScope || !passportQuery.data) return null;
    const allowed = new Set(passportQuery.data.allowed_equipment_ids);
    // Прежний выбор старого случая остаётся видимым при редактировании
    if (currentData?.id && currentId) {
      const byId = new Map(allEquipment.map((item) => [item.id, item]));
      let id = Number(currentId);
      const seen = new Set();
      while (byId.has(id) && !seen.has(id)) {
        seen.add(id);
        allowed.add(id);
        id = byId.get(id).parent_id;
      }
    }
    return allowed;
  }, [
    passportScope,
    passportQuery.data,
    currentData?.id,
    currentId,
    allEquipment,
  ]);
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
      {passportScope && !currentData?.section_mask && (
        <p className="text-xs text-slate-500">
          Выберите секцию для выбора оборудования из паспорта
        </p>
      )}
      {passportScope && currentData?.section_mask && passportQuery.isError && (
        <p role="alert" className="text-xs text-red-700">
          Не удалось загрузить состав паспорта
          <button
            type="button"
            onClick={() => passportQuery.refetch()}
            className="ml-2 underline"
          >
            Повторить
          </button>
        </p>
      )}
      {passportScope &&
        currentData?.section_mask &&
        !passportQuery.data &&
        !passportQuery.isError && (
          <p className="text-xs text-slate-500">
            Загрузка оборудования выбранных секций…
          </p>
        )}
      <div className="grid grid-cols-1 gap-3">
        {visibleIndices.map((i) => (
          <EquipmentLevelSelector
            key={i}
            index={i}
            label={mode === "new" && i === 3 ? "Компонент" : labels[i]}
            value={levels[`lvl${i}`]}
            options={getFilteredOptions(i).filter(
              (item) => !allowedIds || allowedIds.has(item.id),
            )}
            isDisabled={equipmentWithLevels.length === 0 || classifierLoading}
            onChange={(id) => handleLevelSelect(i, id, onSelect)}
            error={i === 3 ? errorDesignation : i === 4 ? errorElement : false}
          />
        ))}
      </div>

      {mode === "old" && (
        <>
          <EquipmentFields
            mode={mode}
            passportQuery={passportQuery}
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
            passportQuery={passportQuery}
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
