import { Fragment } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import { STOCK_DOCUMENT_COLUMNS } from "../../constants/omegaStockConfig";
import { formatOmegaStockValue } from "../../utils/omegaStockFormatters";
import { StockColumnFilter } from "./StockColumnFilter";
import { StockDocumentDetails } from "./StockDocumentDetails";

export function StockDocumentTable({
  kind,
  documents,
  expandedDocumentId,
  onSelect,
  filters,
  onFilterChange,
}) {
  const columns = STOCK_DOCUMENT_COLUMNS[kind];

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[1100px] border-collapse text-left text-xs">
        <thead className="sticky top-0 z-10 bg-slate-50 text-[12px] font-black tracking-wide text-slate-500 uppercase">
          <tr>
            {columns.map((column) => {
              return (
                <th
                  key={column.key}
                  className="border-b border-slate-200 px-2 py-2 text-center align-top"
                >
                  <StockColumnFilter
                    kind={kind}
                    column={column}
                    filters={filters}
                    onChange={(selection) =>
                      onFilterChange(column.key, selection)
                    }
                  >
                    <span className="block leading-4">{column.title}</span>
                  </StockColumnFilter>
                </th>
              );
            })}
            <th className="border-b border-slate-200 px-3 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {documents.length === 0 && (
            <tr>
              <td
                colSpan={columns.length + 1}
                className="h-56 px-6 text-center text-sm text-slate-500"
              >
                Документов по выбранным фильтрам нет
              </td>
            </tr>
          )}
          {documents.map((document) => {
            const expanded = expandedDocumentId === document.document_id;
            return (
              <Fragment key={document.document_id}>
                <tr
                  role="button"
                  tabIndex={0}
                  aria-expanded={expanded}
                  onClick={() => onSelect(document.document_id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSelect(document.document_id);
                    }
                  }}
                  className={`cursor-pointer text-slate-700 transition-colors focus:outline-none ${expanded ? "bg-indigo-50 font-semibold" : "bg-white hover:bg-indigo-50 focus:bg-indigo-50"}`}
                  aria-label={`${expanded ? "Свернуть" : "Раскрыть"} документ №${document.number ?? document.document_id}`}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`max-w-64 px-2 py-2 align-top leading-5 break-words ${column.key === "supplier" ? "text-center" : "text-left"}`}
                    >
                      {formatOmegaStockValue(
                        document[column.key],
                        column.format,
                      )}
                    </td>
                  ))}
                  <td className="px-2 py-2 text-indigo-500">
                    {expanded ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </td>
                </tr>
                {expanded && (
                  <tr>
                    <td colSpan={columns.length + 1} className="max-w-0 p-0">
                      <StockDocumentDetails kind={kind} document={document} />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
