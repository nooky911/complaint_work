import React, { useState, useEffect } from "react";
import { Edit, Plus, X, Check, Loader2 } from "lucide-react";

export const EditableInlineControl = ({
  itemId,
  currentName,
  onSave,
  onAdd,
  label,
  className = "",
  disabled = false,
  showButtons = true,
  children,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [tempName, setTempName] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isAdding && !isEditing) {
      setTempName(currentName || "");
    }
  }, [currentName, isAdding, isEditing]);

  const handleStartEditing = () => {
    setTempName(currentName || "");
    setIsEditing(true);
  };

  const handleStartAdding = () => {
    setTempName("");
    setIsAdding(true);
  };

  const handleConfirm = async () => {
    const trimmed = tempName.trim();
    if (!trimmed) {
      setIsEditing(false);
      setIsAdding(false);
      return;
    }

    setIsLoading(true);
    try {
      if (isAdding) {
        await onAdd(trimmed);
      } else {
        await onSave(trimmed);
      }
      setIsAdding(false);
      setIsEditing(false);
    } catch (error) {
      console.error("Ошибка:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setIsAdding(false);
    setTempName(currentName || "");
  };

  // --- РЕЖИМ РЕДАКТИРОВАНИЯ ИЛИ ДОБАВЛЕНИЯ (ИНПУТ) ---
  if (isEditing || isAdding) {
    return (
      <div className={`w-full ${className}`}>
        {label && (
          <label className="mb-1 ml-1 block text-xs font-bold text-slate-500 uppercase">
            {isAdding ? `Новый ${label}` : label}
          </label>
        )}
        <div className="flex items-center gap-2">
          <input
            autoFocus
            className="h-[38px] flex-1 rounded-lg border border-blue-400 px-3 text-sm shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
            value={tempName}
            onChange={(e) => setTempName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleConfirm();
              if (e.key === "Escape") handleCancel();
            }}
            placeholder={isAdding ? "Введите название..." : ""}
          />
          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className="flex h-[38px] w-[38px] items-center justify-center rounded-lg border border-green-200 bg-green-50 text-green-600 transition-colors hover:bg-green-100"
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
            className="flex h-[38px] w-[38px] items-center justify-center rounded-lg border border-red-200 bg-red-50 text-red-600 transition-colors hover:bg-red-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  // --- РЕЖИМ ЧТЕНИЯ (СЕЛЕКТОР) ---
  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label className="mb-1 ml-1 block text-xs font-bold text-slate-500 uppercase">
          {label}
        </label>
      )}
      <div className="flex items-end gap-2">
        {/* СЕЛЕКТОР */}
        <div
          className={`flex-1 ${disabled ? "pointer-events-none opacity-60" : ""}`}
        >
          {children}
        </div>

        {/* КНОПКИ РЕДАКТИРОВАНИЯ И ДОБАВЛЕНИЯ */}
        {showButtons && (
          <div className="flex gap-1">
            <button
              onClick={handleStartEditing}
              disabled={!itemId || disabled}
              className="flex h-[38px] w-[38px] items-center justify-center rounded-lg border border-gray-200 bg-white p-2 text-gray-600 shadow-sm hover:bg-gray-50 disabled:opacity-50"
              title="Редактировать"
            >
              <Edit className="h-4 w-4" />
            </button>

            {/* КНОПКА ДОБАВЛЕНИЯ */}
            <button
              onClick={handleStartAdding}
              className="flex h-[38px] w-[38px] items-center justify-center rounded-lg border border-gray-200 bg-white p-2 text-blue-600 shadow-sm transition-colors hover:bg-blue-50"
              title="Добавить новый"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
