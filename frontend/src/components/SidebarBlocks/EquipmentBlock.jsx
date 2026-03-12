import { MultiSelectField } from "../inputs/index.jsx";
import { REPAIR_FIELDS_LABELS } from "../../constants/labels";

export const EquipmentBlock = ({ filters, options, updateFilter }) => {
  return (
    <>
      <MultiSelectField
        label={REPAIR_FIELDS_LABELS.component}
        selectedValues={filters.component_equipment_id}
        options={options?.components}
        onChange={(v) => updateFilter("component_equipment_id", v)}
        placeholder="Все"
      />
      <MultiSelectField
        label={REPAIR_FIELDS_LABELS.serial_number}
        selectedValues={filters.component_serial_number_old}
        options={options?.component_serial_numbers}
        onChange={(v) => updateFilter("component_serial_number_old", v)}
        placeholder="Все номера"
      />
      <MultiSelectField
        label={REPAIR_FIELDS_LABELS.element}
        selectedValues={filters.element_equipment_id}
        options={options?.elements}
        onChange={(v) => updateFilter("element_equipment_id", v)}
        placeholder="Все"
      />
      <MultiSelectField
        label={REPAIR_FIELDS_LABELS.serial_number}
        selectedValues={filters.element_serial_number_old}
        options={options?.element_serial_numbers}
        onChange={(v) => updateFilter("element_serial_number_old", v)}
        placeholder="Все номера"
      />
      <MultiSelectField
        label={REPAIR_FIELDS_LABELS.malfunction}
        selectedValues={filters.malfunction_id}
        options={options?.malfunctions}
        onChange={(v) => updateFilter("malfunction_id", v)}
        placeholder="Все виды"
      />
    </>
  );
};
