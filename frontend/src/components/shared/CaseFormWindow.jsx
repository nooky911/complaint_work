import { Save, Edit, Trash2 } from "lucide-react";

/** Общее окно существующей формы локомотивного и поездного случая */
export function CaseFormWindow({ children, overlays, label = "Случай" }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      {overlays}
      <div
        data-case-window
        role="dialog"
        aria-modal="true"
        aria-label={label}
        className="flex max-h-[95vh] w-full max-w-4xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl"
      >
        {children}
      </div>
    </div>
  );
}

/** Общие действия создания, просмотра и редактирования случая */
export function CaseFormActions({
  creating,
  editing,
  saving,
  uploading = false,
  loading = false,
  canEdit,
  onCancel,
  onSave,
  onEdit,
  onDelete,
}) {
  return (
    <div className="flex justify-end gap-3 border-t border-gray-200 bg-gray-50 px-6 py-4">
      {!creating && !editing && canEdit && onDelete && (
        <button
          onClick={onDelete}
          disabled={loading}
          className="mr-auto flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50 disabled:opacity-50"
        >
          <Trash2 className="h-4 w-4" /> Удалить случай
        </button>
      )}
      <button
        onClick={onCancel}
        disabled={saving || uploading}
        className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 disabled:opacity-50"
      >
        {creating || editing ? "Отмена" : "Закрыть"}
      </button>
      {creating || editing ? (
        <button
          onClick={onSave}
          disabled={saving || loading || uploading}
          className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white shadow-md transition-all ${saving || loading || uploading ? "cursor-not-allowed bg-slate-300 opacity-80 shadow-none" : "bg-green-600 hover:bg-green-700 active:scale-95"}`}
        >
          {uploading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Загрузка файлов...
            </>
          ) : saving ? (
            creating ? (
              "Создание случая..."
            ) : (
              "Сохранение..."
            )
          ) : (
            <>
              <Save className="h-4 w-4" />
              {creating ? "Создать случай" : "Сохранить"}
            </>
          )}
        </button>
      ) : (
        canEdit && (
          <button
            onClick={onEdit}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-[#0064fe] px-4 py-2 text-sm font-medium text-white shadow-md transition-all hover:bg-blue-700 active:scale-95 disabled:opacity-50"
          >
            <Edit className="h-4 w-4" />
            Редактировать
          </button>
        )
      )}
    </div>
  );
}
