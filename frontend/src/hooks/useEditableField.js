export const useEditableField = (value, onChange, type = "text") => {
  const handleChange = (e) => {
    const val = e.target.value;
    if (type === "number") {
      onChange(val === "" ? null : Number(val));
    } else {
      onChange(val);
    }
  };

  const displayValue = value === null || value === undefined ? "" : value;

  return {
    handleChange,
    displayValue,
  };
};
