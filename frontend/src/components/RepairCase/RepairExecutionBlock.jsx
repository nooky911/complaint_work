import React from "react";
import { Settings } from "lucide-react";
import { formatDate, formatEquipmentName } from "../../utils/formatters";
import { DataField } from "../inputs/DataField.jsx";
import { RepairExecutionEditor } from "../EditableFields";
import { BLOCK_TITLES, REPAIR_FIELDS_LABELS } from "../../constants/labels";

export const RepairExecutionBlock = ({
  isEditing,
  currentData,
  updateField,
  references,
  allEquipment = [],
  faultyHierarchy,
  blockType,
  showError,
  validation,
}) => {
  const repairTypeId = Number(
    currentData.repair_type?.id || currentData.repair_type_id,
  );
  const showComponent = repairTypeId === 1 || repairTypeId === 2;
  const showElement = repairTypeId === 3;

  const getCorrectName = (id, fallbackObject) => {
    const targetId = id || fallbackObject?.id;
    if (!targetId) return "—";

    const item = allEquipment.find((e) => e.id === Number(targetId));
    if (!item) return fallbackObject?.name || "—";

    return item.name;
  };

  return (
    <div className="space-y-1">
      <div className="relative mb-3 flex items-center gap-2 rounded-lg border border-emerald-100 bg-gradient-to-r from-emerald-50 to-white px-3 py-2 shadow-md">
        <div
          className={`absolute top-0 bottom-0 left-0 w-1 rounded-l-lg ${
            isEditing ? "bg-emerald-600" : "bg-emerald-600"
          }`}
        ></div>

        <Settings
          className={`h-4 w-4 ${isEditing ? "text-emerald-500" : "text-emerald-500"}`}
        />
        <h3
          className={`text-xs font-bold tracking-wider uppercase ${
            isEditing ? "text-emerald-700" : "text-emerald-700"
          }`}
        >
          {BLOCK_TITLES.repair_block}
        </h3>
      </div>

      {isEditing ? (
        <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-200/50 p-3 shadow-sm">
          <RepairExecutionEditor
            isEditing={isEditing}
            currentData={currentData}
            updateField={updateField}
            references={references}
            allEquipment={allEquipment}
            faultyHierarchy={faultyHierarchy}
            blockType={blockType}
            showError={showError}
            validation={validation}
          />
        </div>
      ) : (
        <div className="space-y-3 rounded-2xl border border-slate-100 bg-slate-200/50 p-3 shadow-sm">
          {/* Инфо о ремонте */}
          <div className="grid grid-cols-2 gap-4">
            <DataField
              label={REPAIR_FIELDS_LABELS.repair_type}
              value={currentData.repair_type?.name}
            />
            <DataField
              label={REPAIR_FIELDS_LABELS.performed_by}
              value={currentData.performed_by?.name}
            />
          </div>

          {/* Владелец и направление */}
          <div className="grid grid-cols-2 gap-4">
            <DataField
              label={REPAIR_FIELDS_LABELS.equipment_owner}
              value={currentData.equipment_owner?.name}
            />
            <DataField
              label={REPAIR_FIELDS_LABELS.destination}
              value={currentData.destination?.name}
            />
          </div>

          {showComponent && (
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-1">
                <DataField
                  label={REPAIR_FIELDS_LABELS.new_component}
                  value={formatEquipmentName(
                    getCorrectName(
                      currentData.new_component_equipment_id,
                      currentData.new_component_equipment,
                    ),
                    currentData.new_component_quantity ||
                      currentData.component_quantity,
                  )}
                />
              </div>
              <DataField
                label={REPAIR_FIELDS_LABELS.serial_number}
                value={currentData.component_serial_number_new}
              />
              <DataField
                label={REPAIR_FIELDS_LABELS.manufacture_date}
                value={formatDate(currentData.component_manufacture_date_new)}
              />
            </div>
          )}

          {showElement && (
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-1">
                <DataField
                  label={REPAIR_FIELDS_LABELS.new_element}
                  value={formatEquipmentName(
                    getCorrectName(
                      currentData.new_element_equipment_id,
                      currentData.new_element_equipment,
                    ),
                    currentData.new_element_quantity ||
                      currentData.element_quantity,
                  )}
                />
              </div>
              <DataField
                label={REPAIR_FIELDS_LABELS.serial_number}
                value={currentData.element_serial_number_new}
              />
              <DataField
                label={REPAIR_FIELDS_LABELS.manufacture_date}
                value={formatDate(currentData.element_manufacture_date_new)}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
