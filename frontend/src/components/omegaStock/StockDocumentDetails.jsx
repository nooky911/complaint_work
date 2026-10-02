import { FileText, X } from "lucide-react";
import { useEffect } from "react";

import { omegaStockFileUrl } from "../../api/omegaStock";
import {
  STOCK_DOCUMENT_COLUMNS,
  STOCK_ITEM_COLUMNS,
} from "../../constants/omegaStockConfig";
import {
  useOmegaStockFiles,
  useOmegaStockItems,
} from "../../hooks/api/useOmegaStockApi";
import { formatOmegaStockValue } from "../../utils/omegaStockFormatters";

export function StockDocumentDetails({ kind, document, onClose }) {
  const documentId = document.document_id;
  const {
    data: items = [],
    isLoading: itemsLoading,
    isError: itemsError,
  } = useOmegaStockItems(kind, documentId);
  const {
    data: files = [],
    isLoading: filesLoading,
    isError: filesError,
  } = useOmegaStockFiles(kind, documentId);

  useEffect(() => {
    const closeOnEscape = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.document.addEventListener("keydown", closeOnEscape);
    return () => window.document.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-slate-900/35"
      onMouseDown={onClose}
    >
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={`Документ №${document.number ?? documentId}`}
        onMouseDown={(event) => event.stopPropagation()}
        className="flex h-full w-full max-w-4xl flex-col bg-gray-50 shadow-2xl"
      >
        <div className="flex items-center justify-between gap-4 border-b border-slate-200 bg-white px-5 py-4 md:px-7">
          <div>
            <p className="text-[11px] font-black tracking-wider text-indigo-600 uppercase">
              Складской документ
            </p>
            <h2 className="mt-1 text-lg font-bold text-slate-900">
              №{document.number ?? documentId}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Закрыть документ"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto p-5 md:p-7">
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="mb-4 text-sm font-black text-slate-900">
              Общие сведения
            </h3>
            <dl className="grid gap-x-6 gap-y-4 sm:grid-cols-2">
              {STOCK_DOCUMENT_COLUMNS[kind].map((column) => (
                <div key={column.key} className="min-w-0">
                  <dt className="text-[10px] font-black tracking-wide text-slate-400 uppercase">
                    {column.title}
                  </dt>
                  <dd className="mt-1 text-sm font-medium break-words text-slate-800">
                    {formatOmegaStockValue(document[column.key], column.format)}
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-5 py-4">
              <h3 className="text-sm font-black text-slate-900">
                Состав документа
              </h3>
            </div>
            {itemsLoading ? (
              <p className="p-5 text-sm text-slate-500">Загрузка состава...</p>
            ) : itemsError ? (
              <p className="p-5 text-sm text-red-600">
                Не удалось загрузить состав документа
              </p>
            ) : items.length === 0 ? (
              <p className="p-5 text-sm text-slate-500">
                В документе нет позиций
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px] text-left text-xs">
                  <thead className="bg-slate-50 text-[10px] font-black tracking-wide text-slate-500 uppercase">
                    <tr>
                      {STOCK_ITEM_COLUMNS[kind].map((column) => (
                        <th key={column.key} className="px-5 py-3">
                          {column.title}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {items.map((item) => (
                      <tr key={`${item.item_id}-${item.lot_movement_id ?? 0}`}>
                        {STOCK_ITEM_COLUMNS[kind].map((column) => (
                          <td
                            key={column.key}
                            className="max-w-80 px-5 py-3 align-top break-words text-slate-700"
                          >
                            {formatOmegaStockValue(
                              item[column.key],
                              column.format,
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="mb-3 text-sm font-black text-slate-900">Файлы</h3>
            {filesLoading ? (
              <p className="text-sm text-slate-500">Загрузка файлов...</p>
            ) : filesError ? (
              <p className="text-sm text-red-600">Не удалось загрузить файлы</p>
            ) : files.length === 0 ? (
              <p className="text-sm text-slate-500">Вложений нет</p>
            ) : (
              <div className="space-y-2">
                {files.map((file) => (
                  <a
                    key={file.id}
                    href={omegaStockFileUrl(kind, documentId, file.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-indigo-600 hover:bg-indigo-50"
                  >
                    <FileText className="h-4 w-4" />
                    {file.name}
                  </a>
                ))}
              </div>
            )}
          </section>
        </div>
      </aside>
    </div>
  );
}
