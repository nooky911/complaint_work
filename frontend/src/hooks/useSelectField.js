export const useSelectField = (value, onChange) => {
  const handleChange = (e) => {
    onChange(e.target.value ? Number(e.target.value) : null);
  };

  const displayValue = value || "";

  return {
    handleChange,
    displayValue,
  };
};
