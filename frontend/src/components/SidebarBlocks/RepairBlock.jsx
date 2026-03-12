import { MultiSelectField } from "../inputs/index.jsx";
import { REPAIR_FIELDS_LABELS } from "../../constants/labels";

export const RepairBlock = ({ filters, options, updateFilter }) => {
  return (
    <>
      {/* Секция нового оборудования */}
      <div className="space-y-3">
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.new_component}
          selectedValues={filters.new_component_equipment_id}
          options={options?.new_components}
          onChange={(v) => updateFilter("new_component_equipment_id", v)}
          placeholder="Все компоненты"
        />
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.serial_number}
          selectedValues={filters.component_serial_number_new}
          options={options?.component_serial_numbers_new}
          onChange={(v) => updateFilter("component_serial_number_new", v)}
          placeholder="Все номера"
        />
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.new_element}
          selectedValues={filters.new_element_equipment_id}
          options={options?.new_elements}
          onChange={(v) => updateFilter("new_element_equipment_id", v)}
          placeholder="Все элементы"
        />
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.serial_number}
          selectedValues={filters.element_serial_number_new}
          options={options?.element_serial_numbers_new}
          onChange={(v) => updateFilter("element_serial_number_new", v)}
          placeholder="Все номера"
        />
      </div>

      {/* Разделитель */}
      <div className="h-px w-full bg-slate-300/30" />

      {/* Секция деталей ремонта */}
      <div className="space-y-3">
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.repair_type}
          selectedValues={filters.repair_type_id}
          options={options?.repair_types}
          onChange={(v) => updateFilter("repair_type_id", v)}
          placeholder="Все виды ремонта"
        />
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.performed_by}
          selectedValues={filters.performed_by_id}
          options={options?.performed_by}
          onChange={(v) => updateFilter("performed_by_id", v)}
          placeholder="Кем выполнен"
        />
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.destination}
          selectedValues={filters.destination_id}
          options={options?.destinations}
          onChange={(v) => updateFilter("destination_id", v)}
          placeholder="Все"
        />
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.equipment_owner}
          selectedValues={filters.equipment_owner_id}
          options={options?.equipment_owners}
          onChange={(v) => updateFilter("equipment_owner_id", v)}
          placeholder="Все"
        />
      </div>
    </>
  );
};
