import { MultiSelectField } from "../inputs/index.jsx";
import { REPAIR_FIELDS_LABELS } from "../../constants/labels";

export const StatusBlock = ({
  filters,
  options,
  updateFilter,
  userOptions,
}) => {
  return (
    <>
      <MultiSelectField
        label={REPAIR_FIELDS_LABELS.status}
        selectedValues={filters.status}
        options={options?.statuses}
        onChange={(v) => updateFilter("status", v)}
        placeholder="Любой статус"
      />
      <MultiSelectField
        label="Ответственный"
        selectedValues={filters.user_id}
        options={userOptions}
        onChange={(v) => updateFilter("user_id", v)}
        placeholder="Все сотрудники"
      />
    </>
  );
};
