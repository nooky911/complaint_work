import { ChevronRight } from "lucide-react";

import { STOCK_DOCUMENT_COLUMNS } from "../../constants/omegaStockConfig";
import { formatOmegaStockValue } from "../../utils/omegaStockFormatters";

export function StockDocumentTable({ kind, documents, onSelect }) {
  const columns = STOCK_DOCUMENT_COLUMNS[kind];

  if (documents.length === 0) {
    return (
      <div className="flex min-h-56 items-center justify-center px-6 text-center text-sm text-slate-500">
        Документов пока нет
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[1100px] border-collapse text-left text-xs">
        <thead className="sticky top-0 z-10 bg-slate-50 text-[10px] font-black tracking-wide text-slate-500 uppercase">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className="border-b border-slate-200 px-4 py-3"
              >
                {column.title}
              </th>
            ))}
            <th className="border-b border-slate-200 px-3 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {documents.map((document) => (
            <tr
              key={document.document_id}
              role="button"
              tabIndex={0}
              onClick={() => onSelect(document)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelect(document);
                }
              }}
              className="cursor-pointer bg-white text-slate-700 transition-colors hover:bg-indigo-50 focus:bg-indigo-50 focus:outline-none"
              aria-label={`Открыть документ №${document.number ?? document.document_id}`}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className="max-w-64 px-4 py-3 align-top leading-5 break-words"
                >
                  {formatOmegaStockValue(document[column.key], column.format)}
                </td>
              ))}
              <td className="px-3 py-3 text-indigo-500">
                <ChevronRight className="h-4 w-4" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
