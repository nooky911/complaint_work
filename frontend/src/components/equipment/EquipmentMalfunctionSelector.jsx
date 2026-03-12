import React from "react";

import { SearchableSelect } from "../inputs";
import { AutoResizingTextarea } from "../Components";
import { Tooltip } from "../../utils/Tooltip";
import { REPAIR_FIELDS_LABELS } from "../../constants/labels";

export const EquipmentMalfunctionSelector = ({
  activeId,
  currentData,
  updateField,
  references,
  errorMalfunction,
}) => {
  const { equipment_malfunctions = [], malfunctions = [] } = references || {};

  const allowedMalfunctionIds = equipment_malfunctions
    .filter((link) => link.equipment_id === activeId)
    .map((link) => link.malfunction_id);

  const finalMalfunctionOptions = malfunctions.filter((m) =>
    allowedMalfunctionIds.includes(m.id),
  );

  return (
    <div className="space-y-1.5">
      <Tooltip
        text={
          finalMalfunctionOptions.find(
            (m) => m.id === currentData?.malfunction_id,
          )?.name
        }
      >
        <SearchableSelect
          label={REPAIR_FIELDS_LABELS.malfunction}
          options={finalMalfunctionOptions}
          value={currentData?.malfunction_id}
          onChange={(id) => updateField("malfunction_id", id)}
          placeholder={
            activeId
              ? "Выберите неисправность..."
              : "Сначала выберите оборудование"
          }
          isDisabled={!activeId || finalMalfunctionOptions.length === 0}
          error={errorMalfunction}
        />
      </Tooltip>
      <div className="flex flex-col">
        <AutoResizingTextarea
          label={REPAIR_FIELDS_LABELS.note}
          value={currentData?.notes}
          onChange={(val) => updateField("notes", val)}
          isDisabled={false}
          placeholder="-"
          className="bg-white"
        />
      </div>
    </div>
  );
};
