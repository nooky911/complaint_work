import React from "react";

import { useEquipmentHierarchy } from "../hooks/useEquipmentHierarchy";
import { useToast } from "../hooks/useToast";
import { EquipmentValidation } from "../utils/equipmentValidation";
import {
  EquipmentLevelSelector,
  EquipmentMalfunctionSelector,
} from "./equipment";
import { EditableInlineControl } from "./inputs";
import { MultiAttachInlineControl } from "./inputs/MultiAttachInlineControl";
import { ErrorToast } from "./Toast/ErrorToast";
import {
  useCreateEquipment,
  useUpdateEquipment,
  useUpdateMalfunction,
  useAttachMalfunctions,
} from "../hooks/useEquipmentMutations";

export const SimpleEquipmentEditor = ({
  isEditing,
  currentId,
  onSelect,
  currentData,
  updateField,
  references,
  allEquipment = [],
  disableAutoFill = false,
}) => {
  const { toasts, addToast, removeToast, showError, showSuccess } = useToast();

  // Мутации
  const createEquipmentMutation = useCreateEquipment();
  const updateEquipmentMutation = useUpdateEquipment();
  const updateMalfunctionMutation = useUpdateMalfunction();
  const attachMalfunctionsMutation = useAttachMalfunctions();

  const {
    levels,
    labels,
    equipmentWithLevels,
    activeId,
    handleLevelSelect,
    getFilteredOptions,
  } = useEquipmentHierarchy({
    currentId,
    allEquipment,
    mode: "old",
    initialLevels: null,
    currentData,
    updateField,
    isEditing,
    disableAutoFill,
  });

  const handleSaveEquipmentName = async (equipmentId, newName) => {
    try {
      await updateEquipmentMutation.mutateAsync({
        id: equipmentId,
        name: newName,
      });
      showSuccess("Успешно", `Оборудование "${newName}" обновлено`);
    } catch (error) {
      console.error("Ошибка при обновлении оборудования:", error);
      const errorMessage =
        error.response?.data?.detail ||
        "Произошла ошибка при обновлении оборудования";
      showError("Ошибка редактирования", errorMessage);
    }
  };

  const handleCreateEquipment = async (levelIndex, newName) => {
    const parentId = levelIndex > 0 ? levels[`lvl${levelIndex - 1}`] : null;

    const validation = EquipmentValidation.validateCreateEquipment(
      newName,
      parentId,
      allEquipment,
    );
    if (!validation.isValid) {
      validation.errors.forEach((error) => {
        addToast({
          type: error.type,
          title: "Ошибка создания",
          message: error.message,
        });
      });
      return;
    }

    try {
      await createEquipmentMutation.mutateAsync({ name: newName, parentId });
      showSuccess("Успешно", `Оборудование "${newName}" создано`);
    } catch (error) {
      console.error("Ошибка при создании оборудования:", error);
      const errorMessage =
        error.response?.data?.detail ||
        "Произошла ошибка при создании оборудования";
      showError("Ошибка создания", errorMessage);
    }
  };

  const handleSaveMalfunctionName = async (malfId, newName) => {
    const validation = EquipmentValidation.validateCreateMalfunction(
      newName,
      references.malfunctions || [],
    );
    if (!validation.isValid) {
      validation.errors.forEach((error) => {
        addToast({
          type: error.type,
          title: "Ошибка редактирования",
          message: error.message,
        });
      });
      return;
    }

    try {
      await updateMalfunctionMutation.mutateAsync({
        id: malfId,
        name: newName,
      });
      showSuccess("Успешно", `Неисправность "${newName}" обновлена`);
    } catch (error) {
      console.error("Ошибка при обновлении неисправности:", error);
      const errorMessage =
        error.response?.data?.detail ||
        "Произошла ошибка при обновлении неисправности";
      showError("Ошибка редактирования", errorMessage);
    }
  };

  const handleAttachMalfunctions = async (payload) => {
    const eqId = currentData.id;
    if (!eqId) {
      showError("Ошибка", "Сначала выберите оборудование");
      return;
    }

    if (payload.new_names && payload.new_names.length > 0) {
      for (const newName of payload.new_names) {
        const validation = EquipmentValidation.validateCreateMalfunction(
          newName,
          references.malfunctions || [],
        );
        if (!validation.isValid) {
          validation.errors.forEach((error) => {
            addToast({
              type: error.type,
              title: "Ошибка добавления",
              message: error.message,
            });
          });
          return;
        }
      }
    }

    try {
      await attachMalfunctionsMutation.mutateAsync({
        equipmentId: eqId,
        payload,
      });

      const totalMalfunctions =
        (payload.malfunction_ids?.length || 0) +
        (payload.new_names?.length || 0);
      showSuccess(
        "Успешно",
        `Привязано ${totalMalfunctions} неисправностей к оборудованию`,
      );
    } catch (error) {
      console.error("Ошибка при привязке неисправностей:", error);
      const errorMessage =
        error.response?.data?.detail ||
        "Произошла ошибка при привязке неисправностей";
      showError("Ошибка привязки", errorMessage);
    }
  };

  if (!isEditing) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4">
        {[0, 1, 2, 3, 4].map((i) => {
          const isVisible = i === 0 || !!levels[`lvl${i - 1}`];
          if (!isVisible) return null;

          return (
            <div
              key={i}
              className="animate-in fade-in slide-in-from-top-1 duration-200"
            >
              <EditableInlineControl
                itemId={levels[`lvl${i}`]}
                label={labels[i]}
                currentName={
                  equipmentWithLevels.find((e) => e.id === levels[`lvl${i}`])
                    ?.name || ""
                }
                onSave={(newName) =>
                  handleSaveEquipmentName(levels[`lvl${i}`], newName)
                }
                onAdd={(newName) => handleCreateEquipment(i, newName)}
                showButtons={i >= 1}
              >
                <EquipmentLevelSelector
                  index={i}
                  label=""
                  value={levels[`lvl${i}`]}
                  options={getFilteredOptions(i)}
                  isDisabled={equipmentWithLevels.length === 0}
                  onChange={(id) => handleLevelSelect(i, id, onSelect)}
                />
              </EditableInlineControl>
            </div>
          );
        })}
      </div>

      {/* СЕКЦИЯ НЕИСПРАВНОСТЕЙ */}
      {!!levels.lvl3 && (
        <div className="animate-in zoom-in-95 mt-4 duration-300">
          <MultiAttachInlineControl
            itemId={currentData.malfunction_id}
            label="Неисправности"
            currentName={
              references.malfunctions.find(
                (m) => m.id === currentData.malfunction_id,
              )?.name || ""
            }
            options={references.malfunctions}
            onSave={(newName) =>
              handleSaveMalfunctionName(currentData.malfunction_id, newName)
            }
            onAttach={handleAttachMalfunctions}
          >
            <EquipmentMalfunctionSelector
              activeId={activeId}
              currentData={currentData}
              updateField={updateField}
              references={references}
              hideNotes={true}
              label=""
            />
          </MultiAttachInlineControl>
        </div>
      )}

      {/* Контейнер для тостов */}
      {toasts.map((toast) => (
        <ErrorToast
          key={toast.id}
          show={true}
          title={toast.title}
          message={toast.message}
          type={toast.type}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  );
};
