import {
  DatePickerField,
  MultiSelectField,
  SectionSelect,
} from "../inputs";
import { REPAIR_FIELDS_LABELS } from "../../constants/labels";

export const LocomotiveBlock = ({ filters, options, updateFilter }) => {
  return (
    <>
      <div className="grid grid-cols-2 gap-4">
        <DatePickerField
          label="С даты"
          value={filters.date_from || ""}
          onChange={(v) => updateFilter("date_from", v)}
          isEditing={true}
        />
        <DatePickerField
          label="По дату"
          value={filters.date_to || ""}
          onChange={(v) => updateFilter("date_to", v)}
          isEditing={true}
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.locomotive_model}
          selectedValues={filters.locomotive_model_id}
          options={options?.locomotive_models}
          onChange={(v) => updateFilter("locomotive_model_id", v)}
          placeholder="Все"
        />
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.locomotive_number}
          selectedValues={filters.locomotive_number}
          options={options?.locomotive_numbers}
          onChange={(v) => updateFilter("locomotive_number", v)}
          placeholder="Все"
        />
      </div>

      <SectionSelect
        label={REPAIR_FIELDS_LABELS.section}
        mask={filters.section_mask}
        onChange={(v) => updateFilter("section_mask", v)}
        isEditing={true}
      />

      <MultiSelectField
        label={REPAIR_FIELDS_LABELS.regional_center}
        selectedValues={filters.regional_center_id}
        options={options?.regional_centers}
        onChange={(v) => updateFilter("regional_center_id", v)}
        placeholder="Все центры"
      />
    </>
  );
};
