import React from "react";
import { SearchableSelect } from "../inputs";

export const EquipmentLevelSelector = ({
  index,
  label,
  value,
  options,
  isDisabled,
  onChange,
  error,
}) => {
  return (
    <SearchableSelect
      key={`level-${index}`}
      label={label}
      placeholder="Выберите из списка..."
      options={options}
      value={value}
      isDisabled={isDisabled}
      onChange={onChange}
      error={error}
    />
  );
};
