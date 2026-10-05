import { FileText } from "lucide-react";

import { omegaStockFileUrl } from "../../api/omegaStock";
import { STOCK_ITEM_COLUMNS } from "../../constants/omegaStockConfig";
import {
  useOmegaStockFiles,
  useOmegaStockItems,
} from "../../hooks/api/useOmegaStockApi";
import { formatOmegaStockValue } from "../../utils/omegaStockFormatters";

export function StockDocumentDetails({ kind, document }) {
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

  return (
    <div className="w-full min-w-0 max-w-[calc(100vw-8rem)] space-y-3 border-l-4 border-indigo-400 bg-slate-100 px-3 py-3 md:px-4">
      <section className="min-w-0 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-4 py-3">
          <h3 className="text-sm font-black text-slate-900">Состав документа</h3>
        </div>
        {itemsLoading ? (
          <p className="p-5 text-sm text-slate-500">Загрузка состава...</p>
        ) : itemsError ? (
          <p className="p-5 text-sm text-red-600">
            Не удалось загрузить состав документа
          </p>
        ) : items.length === 0 ? (
          <p className="p-5 text-sm text-slate-500">В документе нет позиций</p>
        ) : (
          <div className="w-full max-w-full overflow-x-auto overscroll-x-contain">
            <table className="w-max min-w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] font-black tracking-wide text-slate-500 uppercase">
                <tr>
                  {STOCK_ITEM_COLUMNS[kind].map((column) => (
                    <th key={column.key} className="whitespace-nowrap px-3 py-2">
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
                        className="max-w-80 px-3 py-2 align-top break-words text-slate-700"
                      >
                        {formatOmegaStockValue(item[column.key], column.format)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-sm font-black text-slate-900">Файлы</h3>
        {filesLoading ? (
          <p className="text-sm text-slate-500">Загрузка файлов...</p>
        ) : filesError ? (
          <p className="text-sm text-red-600">Не удалось загрузить файлы</p>
        ) : files.length === 0 ? (
          <p className="text-sm text-slate-500">Вложений нет</p>
        ) : (
          <div className="flex flex-wrap gap-2">
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
  );
}
