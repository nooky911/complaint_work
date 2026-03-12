import { MultiSelectField } from "../inputs/index.jsx";

export const SupplierBlock = ({ filters, options, updateFilter }) => {
  return (
    <MultiSelectField
      selectedValues={filters.supplier_id}
      options={options?.suppliers}
      onChange={(v) => updateFilter("supplier_id", v)}
      placeholder="Все поставщики"
    />
  );
};
