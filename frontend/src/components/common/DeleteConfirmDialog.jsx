import React from "react";
import { AlertTriangle } from "lucide-react";

export const DeleteConfirmDialog = ({
  show,
  fileName,
  isDeleting,
  onCancel,
  onConfirm,
}) => {
  if (!show) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div
        className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center gap-3 text-red-600">
          <AlertTriangle className="h-6 w-6" />
          <h3 className="text-lg font-bold">
            Вы точно хотите удалить файл?
          </h3>
        </div>
        <p className="mb-2 text-sm text-gray-600">
          {fileName || "Файл"}
        </p>
        <p className="mb-6 text-sm text-gray-600">Действие необратимо.</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={() => {
              if (isDeleting) return;
              onCancel();
            }}
            disabled={isDeleting}
            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          >
            Нет
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-md hover:bg-red-700 disabled:opacity-50"
          >
            {isDeleting ? "Удаление..." : "Да, удалить"}
          </button>
        </div>
      </div>
    </div>
  );
};
