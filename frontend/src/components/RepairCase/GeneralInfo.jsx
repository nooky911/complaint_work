import React from "react";
import { Train } from "lucide-react";
import {
  formatDate,
  formatSectionMask,
  formatToDB,
  getText,
} from "../../utils/formatters";
import {
  DataField,
  SelectField,
  SectionSelect,
  DatePickerField,
  EditableField,
} from "../inputs/index.jsx";
import { BLOCK_TITLES, REPAIR_FIELDS_LABELS } from "../../constants/labels";

export const GeneralInfo = ({
  isEditing,
  currentData,
  repairCase,
  updateField,
  references,
  validation,
  showError,
}) => {
  return (
    <div className="space-y-1">
      <div className="relative mb-3 flex items-center gap-2 rounded-lg border border-blue-100 bg-gradient-to-r from-blue-50 to-white px-3 py-2 shadow-md">
        <div className="absolute top-0 bottom-0 left-0 w-1 rounded-l-lg bg-[#6766cc]"></div>
        <Train className="h-4 w-4 text-[#6766ca]" />
        <h3 className="text-xs font-bold tracking-wider text-[#6169ac] uppercase">
          {BLOCK_TITLES.locomotive_block}
        </h3>
      </div>

      <div className="space-y-0.5 rounded-2xl border border-slate-200 bg-slate-200/50 p-3 shadow-sm">
        {/* Ряд 1: Дата */}
        <div className="grid grid-cols-3 gap-4">
          {isEditing ? (
            <DatePickerField
              label={REPAIR_FIELDS_LABELS.fault_date}
              value={currentData?.fault_date}
              isEditing={true}
              onChange={(value) => updateField("fault_date", formatToDB(value))}
              error={showError && validation?.isFaultDateMissing}
            />
          ) : (
            <DataField
              label={REPAIR_FIELDS_LABELS.fault_date}
              value={formatDate(repairCase.fault_date)}
            />
          )}
          <div className="col-span-2" />
        </div>

        {/* Ряд 2: Модель, Номер, Секция */}
        <div className="grid grid-cols-3 gap-4 pt-2">
          {isEditing ? (
            <>
              <SelectField
                label={REPAIR_FIELDS_LABELS.locomotive_model}
                value={currentData?.locomotive_model_id}
                options={references?.locomotive_models}
                isEditing={true}
                onChange={(value) => updateField("locomotive_model_id", value)}
                className="col-span-1"
                error={showError && validation?.isLocoModelMissing}
              />
              <EditableField
                label={REPAIR_FIELDS_LABELS.locomotive_number}
                value={currentData?.locomotive_number}
                isEditing={true}
                onChange={(value) => updateField("locomotive_number", value)}
                className="col-span-1"
              />
              <SectionSelect
                label={REPAIR_FIELDS_LABELS.section}
                isEditing={true}
                mask={currentData?.section_mask}
                onChange={(value) => updateField("section_mask", value)}
                error={showError && validation?.isSectionMissing}
                className="col-span-1"
              />
            </>
          ) : (
            <>
              <DataField
                label={REPAIR_FIELDS_LABELS.locomotive_model}
                value={getText(repairCase.locomotive_model)}
              />
              <DataField
                label={REPAIR_FIELDS_LABELS.locomotive_number}
                value={repairCase.locomotive_number}
              />
              <DataField
                label={REPAIR_FIELDS_LABELS.section}
                value={formatSectionMask(repairCase.section_mask)}
              />
            </>
          )}
        </div>

        {/* Ряд 3: РЦ, Пробег, Выявлено при */}
        <div className="grid grid-cols-3 gap-4 pt-2">
          {isEditing ? (
            <>
              <SelectField
                label={REPAIR_FIELDS_LABELS.regional_center}
                value={currentData?.regional_center_id}
                options={references?.regional_centers}
                isEditing={true}
                onChange={(value) => updateField("regional_center_id", value)}
                className="col-span-1"
                error={showError && validation?.isRegionMissing}
              />
              <EditableField
                label={REPAIR_FIELDS_LABELS.milage}
                value={currentData?.mileage}
                isEditing={true}
                onChange={(value) => updateField("mileage", value)}
                type="number"
                className="col-span-1"
              />
              <SelectField
                label={REPAIR_FIELDS_LABELS.fault_discovered}
                value={currentData?.fault_discovered_at_id}
                options={references?.fault_discovered_at}
                isEditing={true}
                onChange={(value) =>
                  updateField("fault_discovered_at_id", value)
                }
                className="col-span-1"
                error={showError && validation?.isDiscoveredAtMissing}
              />
            </>
          ) : (
            <>
              <DataField
                label={REPAIR_FIELDS_LABELS.regional_center}
                value={getText(repairCase.regional_center)}
              />
              <DataField
                label={REPAIR_FIELDS_LABELS.milage}
                value={
                  repairCase.mileage
                    ? `${repairCase.mileage.toLocaleString("ru-RU")} км`
                    : "—"
                }
              />
              <DataField
                label={REPAIR_FIELDS_LABELS.fault_discovered}
                value={getText(repairCase.fault_discovered_at)}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
};
