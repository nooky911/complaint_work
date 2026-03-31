import React, { useState } from "react";
import { Edit, Plus, X, Check, Loader2 } from "lucide-react";
import { MultiSelectField } from "./MultiSelectField";

export const MultiAttachInlineControl = ({
  itemId,
  currentName,
  options = [],
  onSave,
  onAttach,
  label,
  className = "",
  disabled = false,
  children,
}) => {
  const [mode, setMode] = useState("idle");
  const [tempName, setTempName] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [selectedValues, setSelectedValues] = useState([]);

  const handleStartAttaching = () => {
    setSelectedValues(itemId ? [itemId] : []);
    setMode("attaching");
  };

  const handleStartEditing = () => {
    setTempName(currentName || "");
    setMode("editing");
  };

  const handleStartCreatingNew = () => {
    setTempName("");
    setMode("creating_new");
  };

  const handleCancel = () => {
    setMode("idle");
  };

  const handleConfirmEdit = async () => {
    const trimmed = tempName.trim();
    if (!trimmed) return handleCancel();

    setIsLoading(true);
    await onSave(trimmed);
    setIsLoading(false);
    setMode("idle");
  };

  const handleConfirmNewText = () => {
    const trimmed = tempName.trim();
    if (trimmed && !selectedValues.includes(trimmed)) {
      setSelectedValues((prev) => [...prev, trimmed]);
    }
    setMode("attaching");
  };

  const handleConfirmAttach = async () => {
    setIsLoading(true);
    const malfunction_ids = selectedValues.filter((v) => typeof v === "number");
    const new_names = selectedValues.filter((v) => typeof v === "string");

    await onAttach({ malfunction_ids, new_names });

    setIsLoading(false);
    setMode("idle");
  };

  // --- РЕНДЕР СОСТОЯНИЙ ---

  if (mode === "creating_new" || mode === "editing") {
    return (
      <div className={`w-full ${className}`}>
        {label && (
          <label className="mb-1 ml-1 block text-xs font-bold text-slate-500 uppercase">
            {label}
          </label>
        )}
        <div className="flex gap-2">
          <input
            type="text"
            value={tempName}
            onChange={(e) => setTempName(e.target.value)}
            className="flex-1 rounded-lg border border-indigo-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            placeholder={
              mode === "editing"
                ? "Изменить название..."
                : "Введите новую неисправность..."
            }
            autoFocus
          />
          <button
            onClick={
              mode === "editing" ? handleConfirmEdit : handleConfirmNewText
            }
            disabled={isLoading}
            className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-lg bg-green-600 text-white hover:bg-green-700"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={() =>
              mode === "editing" ? handleCancel() : setMode("attaching")
            }
            disabled={isLoading}
            className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-lg border border-gray-300 bg-white text-gray-600 hover:bg-gray-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  if (mode === "attaching") {
    const customOptions = selectedValues
      .filter((v) => typeof v === "string")
      .map((str) => ({ id: str, name: str }));

    const combinedOptions = [...options, ...customOptions];

    return (
      <div className={`w-full ${className}`}>
        {label && (
          <label className="mb-1 ml-1 block text-xs font-bold text-slate-500 uppercase">
            {label}
          </label>
        )}
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <MultiSelectField
              label=""
              options={combinedOptions}
              selectedValues={selectedValues}
              onChange={setSelectedValues}
              placeholder="Выберите неисправности..."
            />
          </div>
          <div className="flex shrink-0 gap-1">
            <button
              onClick={handleConfirmAttach}
              disabled={isLoading || selectedValues.length === 0}
              className="flex h-[38px] w-[38px] items-center justify-center rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
              title="Сохранить привязки"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )}
            </button>
            <button
              onClick={handleCancel}
              disabled={isLoading}
              className="flex h-[38px] w-[38px] items-center justify-center rounded-lg border border-gray-300 bg-white text-gray-600 hover:bg-gray-50"
              title="Отмена"
            >
              <X className="h-4 w-4" />
            </button>
            <button
              onClick={handleStartCreatingNew}
              disabled={isLoading}
              className="flex h-[38px] w-[38px] items-center justify-center rounded-lg border border-indigo-600 bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
              title="Добавить новую неисправность вручную"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label className="mb-1 ml-1 block text-xs font-bold text-slate-500 uppercase">
          {label}
        </label>
      )}
      <div className="flex items-end gap-2">
        <div
          className={`flex-1 ${disabled ? "pointer-events-none opacity-60" : ""}`}
        >
          {children}
        </div>
        <div className="flex shrink-0 gap-1">
          <button
            onClick={handleStartEditing}
            disabled={!itemId || disabled}
            className="flex h-[38px] w-[38px] items-center justify-center rounded-lg border border-gray-200 bg-white p-2 text-gray-600 shadow-sm hover:bg-gray-50 disabled:opacity-50"
          >
            <Edit className="h-4 w-4" />
          </button>
          <button
            onClick={handleStartAttaching}
            disabled={disabled}
            className="flex h-[38px] w-[38px] items-center justify-center rounded-lg border border-gray-200 bg-white p-2 text-indigo-600 shadow-sm hover:bg-indigo-50"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
