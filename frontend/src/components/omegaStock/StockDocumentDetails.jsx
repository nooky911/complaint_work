import { useEffect, useRef, useState } from "react";
import { Link } from "lucide-react";

import { useAuth } from "../../context/AuthContext";
import { STOCK_ITEM_COLUMNS } from "../../constants/omegaStockConfig";
import { useOmegaStockItems } from "../../hooks/api/useOmegaStockApi";
import { formatOmegaStockValue } from "../../utils/omegaStockFormatters";
import { StockCaseLinkModal } from "./StockCaseLinkModal";
import { StockDocumentFiles } from "./StockDocumentFiles";

export function StockDocumentDetails({ kind, document }) {
  const documentId = document.document_id;
  const { user } = useAuth();
  const [linkOpen, setLinkOpen] = useState(false);
  const topScrollRef = useRef(null);
  const tableScrollRef = useRef(null);
  const [scrollMetrics, setScrollMetrics] = useState({
    width: 0,
    overflowing: false,
  });
  const {
    data: items = [],
    isLoading: itemsLoading,
    isError: itemsError,
  } = useOmegaStockItems(kind, documentId);

  useEffect(() => {
    const scroller = tableScrollRef.current;
    const table = scroller?.firstElementChild;
    if (!scroller || !table) return undefined;

    const observer = new ResizeObserver(() => {
      const width = scroller.scrollWidth;
      const overflowing = width > scroller.clientWidth + 1;
      setScrollMetrics((current) =>
        current.width === width && current.overflowing === overflowing
          ? current
          : { width, overflowing },
      );
    });
    observer.observe(scroller);
    observer.observe(table);
    return () => observer.disconnect();
  }, [kind, items]);

  return (
    <div className="w-full min-w-0 border-l-4 border-indigo-400 bg-slate-200/70 px-3 py-3 md:px-4">
      <section className="min-w-0 overflow-hidden rounded-lg border border-slate-300 bg-slate-50 shadow-sm">
        <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
          <h3 className="text-sm font-black text-slate-900">
            Состав документа
          </h3>
          {["editor", "superadmin"].includes(user?.role) && (
            <button
              type="button"
              onClick={() => setLinkOpen(true)}
              className="inline-flex items-center gap-[6.8px] rounded-lg bg-indigo-600 px-[10.2px] py-[6.8px] text-[11.9px] leading-[17px] font-bold text-white hover:bg-indigo-700"
            >
              <Link className="h-[13.6px] w-[13.6px]" />
              Связать со случаем
            </button>
          )}
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
          <>
            {scrollMetrics.overflowing && (
              <div
                ref={topScrollRef}
                role="region"
                aria-label="Прокрутка состава документа по горизонтали"
                tabIndex={0}
                onScroll={(event) => {
                  if (tableScrollRef.current) {
                    tableScrollRef.current.scrollLeft =
                      event.currentTarget.scrollLeft;
                  }
                }}
                className="h-5 w-full overflow-x-scroll overflow-y-hidden"
              >
                <div style={{ width: scrollMetrics.width, height: 1 }} />
              </div>
            )}
            <div
              ref={tableScrollRef}
              onScroll={(event) => {
                if (topScrollRef.current) {
                  topScrollRef.current.scrollLeft =
                    event.currentTarget.scrollLeft;
                }
              }}
              className="w-full max-w-full overflow-x-auto overscroll-x-contain"
            >
              <table className="w-max min-w-full text-left text-xs">
                <thead className="bg-slate-200 text-[10px] font-black tracking-wide text-slate-600 uppercase">
                  <tr>
                    {STOCK_ITEM_COLUMNS[kind].map((column) => (
                      <th
                        key={column.key}
                        className="px-3 py-2 whitespace-nowrap"
                      >
                        {column.title}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-slate-100">
                  {items.map((item) => (
                    <tr key={`${item.item_id}-${item.lot_movement_id ?? 0}`}>
                      {STOCK_ITEM_COLUMNS[kind].map((column) => (
                        <td
                          key={column.key}
                          className="max-w-80 px-3 py-2 align-top break-words text-slate-700"
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
          </>
        )}
        <div className="px-3 py-3">
          <StockDocumentFiles kind={kind} documentId={documentId} />
        </div>
      </section>
      {linkOpen && (
        <StockCaseLinkModal
          kind={kind}
          document={document}
          onClose={() => setLinkOpen(false)}
        />
      )}
    </div>
  );
}
