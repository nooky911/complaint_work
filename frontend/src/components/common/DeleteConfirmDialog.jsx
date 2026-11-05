import { createPortal } from "react-dom";
import { AlertTriangle } from "lucide-react";

export const DeleteConfirmDialog = ({
  show,
  fileName,
  isDeleting,
  onCancel,
  onConfirm,
  title = "Вы точно хотите удалить файл?",
  message = "Действие необратимо.",
  confirmLabel = "Да, удалить",
  cancelLabel = "Нет",
  busyLabel = "Удаление...",
}) => {
  if (!show) return null;

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <div
        className="animate-in zoom-in-95 w-full max-w-md rounded-xl bg-white p-6 shadow-2xl duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center gap-3 text-red-600">
          <AlertTriangle className="h-6 w-6" />
          <h3 className="text-lg font-bold">{title}</h3>
        </div>
        {fileName !== null && (
          <p className="mb-2 truncate text-sm text-gray-600">{fileName || "Файл"}</p>
        )}
        <p className="mb-6 text-sm text-gray-600">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={() => {
              if (isDeleting) return;
              onCancel();
            }}
            disabled={isDeleting}
            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-md hover:bg-red-700 disabled:opacity-50"
          >
            {isDeleting ? busyLabel : confirmLabel}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
};
