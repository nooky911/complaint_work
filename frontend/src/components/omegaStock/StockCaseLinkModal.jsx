import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Link, LoaderCircle, X } from "lucide-react";

import api from "../../api/api";
import {
  getStockLinkCases,
  linkStockDocumentToCases,
} from "../../api/omegaStock";
import { useAuth } from "../../context/AuthContext";
import { BLOCK_TITLES } from "../../constants/labels";
import { formatApiError, formatDate, formatToDB } from "../../utils/formatters";
import { TtnBlocks } from "../RepairCase/TtnBlocks";
import { StockColumnFilter } from "./StockColumnFilter";
import { StockDocumentFiles } from "./StockDocumentFiles";

const PAGE_SIZE = 25;
const COLUMNS = [
  { key: "display_number", title: "№" },
  { key: "regional_center", title: "РЦ" },
  { key: "locomotive", title: "Локомотив" },
  { key: "equipment", title: "Оборудование" },
  { key: "serial", title: "Зав. № (дата изг-ия)" },
  { key: "supplier", title: "Поставщик" },
  { key: "notification", title: "№ и дата ув-ия" },
  { key: "act", title: "№ и дата РА / АВР" },
];
const FIELDS = { inplant: "ttn_from_rc", outbound: "ttn_to_supplier" };
const PROVIDERS = {
  ttn_to_supplier: "to_supplier_provider_id",
  ttn_from_supplier: "from_supplier_provider_id",
};

/** Выбирает случаи и переносит документ в существующий блок передвижения */
export function StockCaseLinkModal({ kind, document, onClose }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const dialogRef = useRef(null);
  const confirmationRef = useRef(null);
  const [filters, setFilters] = useState({});
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(new Set());
  const [field, setField] = useState(FIELDS[kind] || "");
  const [values, setValues] = useState(() => {
    const number =
      (kind === "receipts" ? document.accompanying_number : document.number) ||
      "";
    const date =
      (kind === "receipts"
        ? document.accompanying_date
        : document.document_date
      )?.slice(0, 10) || "";
    return Object.fromEntries(
      [
        "ttn_replacement",
        "ttn_from_supplier",
        "ttn_from_rc",
        "ttn_to_supplier",
      ].flatMap((key) => [
        [key, number],
        [`${key}_date`, date],
      ]),
    );
  });
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const selectedIds = [...selected].sort((a, b) => a - b);
  const { data, isPending, isError, refetch } = useQuery({
    queryKey: [
      "omega-stock",
      "link-cases",
      user?.id,
      filters,
      page,
      selectedIds,
    ],
    queryFn: () =>
      getStockLinkCases(
        filters,
        (page - 1) * PAGE_SIZE,
        PAGE_SIZE,
        selectedIds,
      ),
    placeholderData: keepPreviousData,
    staleTime: 0,
  });
  const { data: references, isError: referencesError } = useQuery({
    queryKey: ["references", "stock-link-form"],
    queryFn: async () => (await api.get("/references/case-form")).data,
  });
  const mutation = useMutation({
    mutationFn: ({ payload, checking }) =>
      linkStockDocumentToCases(kind, document.document_id, payload, checking),
  });
  const busy = mutation.isPending;

  useEffect(() => {
    if (preview) confirmationRef.current?.focus();
  }, [preview]);

  useEffect(() => {
    const previouslyFocused = window.document.activeElement;
    dialogRef.current?.focus();
    const previousOverflow = window.document.body.style.overflow;
    window.document.body.style.overflow = "hidden";
    return () => {
      window.document.body.style.overflow = previousOverflow;
      previouslyFocused?.focus();
    };
  }, []);

  const resetPreview = () => {
    setPreview(null);
    setError("");
  };
  const updateField = (key, value) => {
    resetPreview();
    setValues((current) => ({ ...current, [key]: value }));
  };
  const changeFilter = (key, selection) => {
    setFilters((current) => {
      const next = { ...current };
      if (selection) next[key] = selection;
      else delete next[key];
      return next;
    });
    setPage(1);
  };
  const toggleCase = (id) => {
    resetPreview();
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };
  const payload = () => ({
    case_ids: [...selected],
    related_field: field,
    number: values[field] || "",
    document_date: formatToDB(values[`${field}_date`]) || "",
    provider_id: PROVIDERS[field]
      ? Number(values[PROVIDERS[field]]) || null
      : null,
  });
  const check = async () => {
    setError("");
    if (!field || selected.size === 0) {
      setError("Выберите случаи и вид документа");
      return;
    }
    if (selected.size > 100) {
      setError("За один перенос можно выбрать до 100 случаев");
      return;
    }
    if (
      !String(values[field] || "").trim() ||
      String(values[field]).length > 50
    ) {
      setError("Укажите номер документа длиной до 50 символов");
      return;
    }
    if (!formatToDB(values[`${field}_date`])) {
      setError("Укажите полную дату документа");
      return;
    }
    if (PROVIDERS[field] && !values[PROVIDERS[field]]) {
      setError("Выберите перевозчика / действие");
      return;
    }
    try {
      setPreview(
        await mutation.mutateAsync({ payload: payload(), checking: true }),
      );
    } catch (err) {
      setError(formatApiError(err, "Не удалось проверить данные для привязки"));
    }
  };
  const apply = async () => {
    setError("");
    try {
      const response = await mutation.mutateAsync({
        payload: {
          ...payload(),
          preview_token: preview.token,
          confirm_overwrite: preview.existing.length > 0,
        },
        checking: false,
      });
      setResult(response);
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["case"] });
      queryClient.invalidateQueries({ queryKey: ["files"] });
      queryClient.invalidateQueries({ queryKey: ["filesGrouped"] });
      queryClient.invalidateQueries({
        queryKey: ["omega-stock", "link-cases"],
      });
    } catch (err) {
      setError(formatApiError(err, "Не удалось прикрепить документ к случаям"));
      setPreview(null);
    }
  };
  const provider = references?.shipping_providers?.find(
    (item) => item.id === Number(values[PROVIDERS[field]]),
  )?.name;
  const newText = [values[field], formatDate(values[`${field}_date`]), provider]
    .filter(Boolean)
    .join(" · ");

  return createPortal(
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-900/60 p-3 backdrop-blur-sm">
      <div
        ref={dialogRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="stock-link-title"
        onKeyDown={(event) => {
          if (!event.currentTarget.contains(event.target)) return;
          if (event.key === "Escape" && !busy) onClose();
          if (event.key === "Tab") {
            const controls = [
              ...event.currentTarget.querySelectorAll(
                'button:not(:disabled), input:not(:disabled), select:not(:disabled), a[href], [tabindex="0"]',
              ),
            ];
            const first = controls[0],
              last = controls[controls.length - 1];
            if (event.shiftKey && window.document.activeElement === first) {
              event.preventDefault();
              last?.focus();
            } else if (
              !event.shiftKey &&
              window.document.activeElement === last
            ) {
              event.preventDefault();
              first?.focus();
            }
          }
        }}
        className={`flex max-h-[94vh] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl outline-none ${result ? "w-fit max-w-full" : "w-full max-w-[1500px]"}`}
      >
        <header className="flex items-center justify-between gap-3 border-b border-slate-200 bg-slate-50 px-5 py-4">
          <h2
            id="stock-link-title"
            className="flex items-center gap-2 text-lg font-bold text-slate-900"
          >
            <Link className="h-5 w-5 text-indigo-600" />
            Связать со случаем
          </h2>
          <button
            type="button"
            aria-label="Закрыть"
            disabled={busy}
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-slate-200 disabled:opacity-40"
          >
            <X className="h-5 w-5" />
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto">
          {result ? (
            <div
              role="status"
              className="m-5 rounded-xl bg-green-50 p-5 text-base text-green-900"
            >
              <p className="mb-2 font-bold">Документ сохранён</p>
              <p>
                Случаев: <b>{result.case_count}</b>
              </p>
              <p>
                Добавлено файлов: <b>{result.added_files}</b>
              </p>
            </div>
          ) : (
            <>
              <fieldset disabled={busy} className="min-w-0">
                <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 text-sm">
                  <span className="font-semibold text-slate-900">
                    Выбрано случаев: {selected.size}
                  </span>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        resetPreview();
                        setSelected(new Set());
                      }}
                      className="text-indigo-700 hover:underline"
                    >
                      Сбросить выбор
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setFilters({});
                        setPage(1);
                      }}
                      className="text-slate-700 hover:underline"
                    >
                      Сбросить фильтры
                    </button>
                  </div>
                </div>
                <div className="max-h-[40vh] overflow-auto border-y border-slate-200">
                  <table className="w-full min-w-[1000px] text-center text-sm text-black">
                    <thead className="sticky top-0 z-10 bg-slate-200">
                      <tr>
                        {COLUMNS.map((column) => (
                          <th key={column.key} className="py-3 font-bold">
                            <StockColumnFilter
                              kind={kind}
                              column={column}
                              filters={filters}
                              caseSelection
                              onChange={(selection) =>
                                changeFilter(column.key, selection)
                              }
                            >
                              {column.title}
                            </StockColumnFilter>
                          </th>
                        ))}
                        <th className="px-4 py-3">Выбрать</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {isPending ? (
                        <tr>
                          <td
                            colSpan={COLUMNS.length + 1}
                            className="p-8 text-slate-600"
                          >
                            Загрузка случаев...
                          </td>
                        </tr>
                      ) : isError ? (
                        <tr>
                          <td
                            colSpan={COLUMNS.length + 1}
                            className="p-8 text-red-700"
                          >
                            Не удалось загрузить случаи{" "}
                            <button
                              type="button"
                              onClick={() => refetch()}
                              className="underline"
                            >
                              Повторить
                            </button>
                          </td>
                        </tr>
                      ) : !data?.items.length ? (
                        <tr>
                          <td
                            colSpan={COLUMNS.length + 1}
                            className="p-8 text-slate-600"
                          >
                            Случаи не найдены
                          </td>
                        </tr>
                      ) : (
                        data.items.map((item) => (
                          <tr
                            key={item.id}
                            className={
                              selected.has(item.id)
                                ? "bg-indigo-50"
                                : "even:bg-slate-50"
                            }
                          >
                            {COLUMNS.map((column) => (
                              <td
                                key={column.key}
                                className="max-w-64 px-3 py-3 align-middle break-words"
                              >
                                {item[column.key] || "—"}
                              </td>
                            ))}
                            <td className="px-4 py-3">
                              <input
                                type="checkbox"
                                aria-label={`Выбрать случай №${item.display_number}`}
                                checked={selected.has(item.id)}
                                onChange={() => toggleCase(item.id)}
                                className="h-5 w-5 cursor-pointer accent-indigo-600"
                              />
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
                <div className="flex items-center justify-end gap-3 px-5 py-2 text-sm text-slate-700">
                  <span>Всего: {data?.total ?? "—"}</span>
                  <button
                    type="button"
                    aria-label="Предыдущая страница"
                    disabled={page === 1 || isPending}
                    onClick={() => setPage(page - 1)}
                    className="rounded p-2 hover:bg-slate-100 disabled:opacity-30"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  Страница {page}
                  <button
                    type="button"
                    aria-label="Следующая страница"
                    disabled={
                      isPending || !data || page * PAGE_SIZE >= data.total
                    }
                    onClick={() => setPage(page + 1)}
                    className="rounded p-2 hover:bg-slate-100 disabled:opacity-30"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
                {selected.size > 0 && (
                  <div className="space-y-4 border-t border-slate-200 px-5 py-4">
                    {kind === "receipts" && (
                      <div className="space-y-3 text-sm text-slate-900">
                        <p>
                          <b>Замена (восполнение)</b> — новое оборудование от
                          поставщика взамен неисправного.{" "}
                          <b>Возврат от поставщика</b> — прежнее оборудование
                          после ремонта.
                        </p>
                        <div className="grid gap-3 md:grid-cols-2">
                          {["ttn_replacement", "ttn_from_supplier"].map(
                            (value) => (
                              <label
                                key={value}
                                className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-300 bg-slate-100 p-3 font-semibold hover:bg-slate-200"
                              >
                                <input
                                  type="radio"
                                  name="stock-document-target"
                                  value={value}
                                  checked={field === value}
                                  onChange={() => {
                                    resetPreview();
                                    setField(value);
                                  }}
                                  className="accent-indigo-600"
                                />
                                {BLOCK_TITLES[value]}
                              </label>
                            ),
                          )}
                        </div>
                      </div>
                    )}
                    {field && (
                      <>
                        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm font-bold text-red-600">
                          ОБЯЗАТЕЛЬНО перепроверь дату и номер
                        </p>
                        <TtnBlocks
                          isEditing
                          ttnData={{ waybill_doc: values }}
                          updateField={updateField}
                          references={references}
                          visibleFields={[field]}
                          dateDisclaimer={
                            kind === "inplant"
                              ? "Здесь указана дата составления ТТН. Дату получения необходимо уточнить в самой ТТН."
                              : undefined
                          }
                        />
                        {referencesError && PROVIDERS[field] && (
                          <p role="alert" className="text-sm text-red-700">
                            Не удалось загрузить перевозчиков / действия.
                            Закройте окно и повторите попытку.
                          </p>
                        )}
                      </>
                    )}
                  </div>
                )}
              </fieldset>
              <section className="space-y-3 border-t border-slate-200 bg-slate-50 px-5 py-4">
                <h3 className="text-sm font-bold text-slate-900">
                  Файлы складского документа
                </h3>
                <StockDocumentFiles
                  kind={kind}
                  documentId={document.document_id}
                />
                {document.note && (
                  <p className="text-sm whitespace-pre-wrap text-slate-900">
                    <b>Примечание склада:</b> {document.note}
                  </p>
                )}
                <p className="text-xs text-slate-600">
                  Все вложения будут сохранены в выбранном блоке каждого случая.
                  Ненужные файлы можно удалить из случая позднее.
                </p>
              </section>
              {preview && (
                <section
                  ref={confirmationRef}
                  tabIndex={-1}
                  className="space-y-3 border-t border-amber-200 bg-amber-50 px-5 py-4 text-sm text-slate-900 outline-none"
                >
                  <h3 className="font-bold">Подтверждение переноса</h3>
                  <div className="space-y-1">
                    <p>
                      {BLOCK_TITLES[field]}: <b>{newText}</b>
                    </p>
                    <p>
                      Случаев: <b>{preview.case_count}</b>
                    </p>
                    <p>
                      Вложений в документе: <b>{preview.file_count}</b>
                    </p>
                  </div>
                  {preview.existing.length > 0 && (
                    <>
                      <p className="font-bold text-amber-900">
                        В следующих случаях блок уже заполнен. Его данные будут
                        заменены, существующие файлы сохранятся.
                      </p>
                      <div className="max-h-48 overflow-auto">
                        <table className="w-full text-left">
                          <thead>
                            <tr>
                              <th className="p-2">№</th>
                              <th className="p-2">Сейчас</th>
                              <th className="p-2">После переноса</th>
                            </tr>
                          </thead>
                          <tbody>
                            {preview.existing.map((item) => (
                              <tr
                                key={item.id}
                                className="border-t border-amber-200"
                              >
                                <td className="p-2">{item.display_number}</td>
                                <td className="p-2">
                                  {[
                                    item.number,
                                    formatDate(item.document_date),
                                    item.provider,
                                  ]
                                    .filter(Boolean)
                                    .join(" · ") || "—"}
                                  <span className="ml-2 text-xs">
                                    Файлов: {item.file_count}
                                  </span>
                                </td>
                                <td className="p-2">{newText}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </section>
              )}
              {error && (
                <p
                  role="alert"
                  className="mx-5 my-3 rounded-lg bg-red-50 p-3 text-sm font-semibold text-red-700"
                >
                  {error}
                </p>
              )}
            </>
          )}
        </div>
        <footer className="flex items-center justify-end gap-3 border-t border-slate-200 bg-white px-5 py-4">
          <button
            type="button"
            disabled={busy}
            onClick={onClose}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-bold text-slate-700 disabled:opacity-40"
          >
            {result ? "Закрыть" : "Отмена"}
          </button>
          {!result && (
            <button
              type="button"
              disabled={busy || !selected.size || !field}
              onClick={preview ? apply : check}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-bold text-white hover:bg-indigo-700 disabled:opacity-40"
            >
              {busy && <LoaderCircle className="h-4 w-4 animate-spin" />}
              {busy
                ? mutation.variables?.checking
                  ? "Проверка..."
                  : "Скачивание и сохранение..."
                : preview
                  ? preview.existing.length
                    ? "Подтвердить замену и прикрепить"
                    : "Подтвердить и прикрепить"
                  : "Проверить данные"}
            </button>
          )}
        </footer>
      </div>
    </div>,
    window.document.body,
  );
}
