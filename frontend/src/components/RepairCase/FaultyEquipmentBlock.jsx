import React from "react";
import { Package } from "lucide-react";
import {
  formatDate,
  formatEquipmentName,
  getText,
} from "../../utils/formatters";
import { DataField } from "../inputs/index.jsx";
import { EquipmentHierarchyEditor } from "../EquipmentHierarchyEditor";
import { BLOCK_TITLES, REPAIR_FIELDS_LABELS } from "../../constants/labels";
import { Tooltip } from "../../utils/Tooltip";

export const FaultyEquipmentBlock = ({
  isEditing,
  repairCase,
  currentData,
  updateField,
  references,
  allEquipment,
  handleEquipmentSelect,
  faultyValidation,
  showError,
  validation,
}) => {
  return (
    <div className="space-y-1">
      <div className="relative mb-3 flex items-center gap-2 rounded-lg border border-blue-100 bg-gradient-to-r from-blue-50 to-white px-3 py-2 shadow-md">
        <div
          className={`absolute top-0 bottom-0 left-0 w-1 rounded-l-lg ${
            isEditing ? "bg-blue-600" : "bg-blue-600"
          }`}
        ></div>
        <Package className="h-4 w-4 text-blue-500" />
        <h3 className="text-xs font-bold tracking-wider text-blue-700 uppercase">
          {BLOCK_TITLES.equipment_block}
        </h3>
      </div>

      {isEditing ? (
        <div className="space-y-2">
          <EquipmentHierarchyEditor
            isEditing={isEditing}
            currentId={
              repairCase.element_equipment?.id ||
              repairCase.component_equipment?.id
            }
            onSelect={handleEquipmentSelect}
            currentData={currentData}
            updateField={updateField}
            references={references}
            allEquipment={allEquipment}
            faultyValidation={faultyValidation}
            showError={showError}
            errorDesignation={showError && validation.isDesignationMissing}
            errorMalfunction={showError && validation.isMalfunctionMissing}
          />
        </div>
      ) : (
        <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-200/50 p-3 shadow-sm">
          <div className="grid grid-cols-3 gap-4">
            <Tooltip
              text={formatEquipmentName(
                repairCase.component_equipment?.name,
                repairCase.component_quantity,
              )}
            >
              <DataField
                label={REPAIR_FIELDS_LABELS.component}
                value={formatEquipmentName(
                  repairCase.component_equipment?.name,
                  repairCase.component_quantity,
                )}
              />
            </Tooltip>

            <DataField
              label={REPAIR_FIELDS_LABELS.serial_number}
              value={repairCase.component_serial_number_old}
            />
            <DataField
              label={REPAIR_FIELDS_LABELS.manufacture_date}
              value={formatDate(repairCase.component_manufacture_date_old)}
            />
          </div>

          {repairCase.element_equipment?.id ||
          repairCase.element_serial_number_old ||
          repairCase.element_manufacture_date_old ? (
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-1">
                <Tooltip
                  text={repairCase.element_equipment?.name?.replace(/_/g, " ")}
                >
                  <DataField
                    label={REPAIR_FIELDS_LABELS.element}
                    value={`${repairCase.element_equipment?.name?.replace(/_/g, " ") || "—"}${
                      repairCase.element_quantity > 1
                        ? ` (${repairCase.element_quantity} шт.)`
                        : ""
                    }`}
                  />
                </Tooltip>
              </div>
              <DataField
                label={REPAIR_FIELDS_LABELS.serial_number}
                value={repairCase.element_serial_number_old}
              />
              <DataField
                label={REPAIR_FIELDS_LABELS.manufacture_date}
                value={formatDate(repairCase.element_manufacture_date_old)}
              />
            </div>
          ) : null}

          <Tooltip text={getText(repairCase.malfunction)}>
            <DataField
              label={REPAIR_FIELDS_LABELS.malfunction}
              value={getText(repairCase.malfunction)}
            />
          </Tooltip>

          {repairCase.notes && (
            <DataField
              label={REPAIR_FIELDS_LABELS.note}
              value={repairCase.notes}
              fullWidth={true}
              isTextArea={true}
            />
          )}
        </div>
      )}
    </div>
  );
};
