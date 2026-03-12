import React from "react";

export function DataField({
  label,
  value,
  fullWidth = false,
  isTextArea = false,
}) {
  return (
    <div className={`${fullWidth ? "w-full" : ""}`}>
      <label className="mb-1 ml-1 block text-xs font-bold text-gray-500 uppercase">
        {label}
      </label>
      <div
        className={`w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-900 shadow-sm ${
          isTextArea
            ? "min-h-[38px] break-words whitespace-pre-wrap"
            : "flex h-[38px] items-center truncate"
        }`}
      >
        {value || "—"}
      </div>
    </div>
  );
}
