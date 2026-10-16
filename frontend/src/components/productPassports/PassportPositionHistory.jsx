import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Loader2, X } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../../context/AuthContext";
import api from "../../api/api";
import { EditableField, SearchableSelect } from "../inputs/index.jsx";
import { isValidManufactureDate } from "../../utils/validators";
import {
  formatDate,
  formatApiError,
  formatFullName,
} from "../../utils/formatters";

/** Показывает историю позиции и форму исправления паспорта */
export function PassportPositionHistory({ passportId, node }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const dialogRef = useRef(null);
  const historyTitleId = useId();

  // Открываем отдельное окно с удержанием фокуса внутри и закрытием по Escape
  useEffect(() => {
    if (!open) return;
    const dialog = dialogRef.current;
    dialog.showModal();
    return () => dialog.close();
  }, [open]);
  const [form, setForm] = useState({
    equipment_id: node.equipment_id,
    serial_number: node.serial_number || "",
    manufacture_date_text: node.manufacture_date || "",
    reason: "",
  });
  /** Закрывает историю и возвращает фокус к кнопке */
  const closeHistory = () => {
    dialogRef.current?.close();
    setOpen(false);
  };
  const history = useQuery({
    queryKey: ["product-passports", passportId, node.id, "history"],
    queryFn: async () =>
      (
        await api.get(
          `/product-passports/${passportId}/nodes/${node.id}/history`,
        )
      ).data,
    enabled: open,
  });
  const types = useQuery({
    queryKey: ["product-passports", passportId, node.id, "types"],
    queryFn: async () =>
      (await api.get(`/product-passports/${passportId}/nodes/${node.id}/types`))
        .data,
    enabled: editing,
  });
  const save = useMutation({
    mutationFn: () =>
      api.patch(`/product-passports/${passportId}/nodes/${node.id}`, {
        ...form,
        expected_version: node.version,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["product-passports"] });
      setEditing(false);
    },
  });
  return (
    <div className="mt-5 space-y-3 border-t border-slate-200 pt-4">
      <div className="flex flex-wrap gap-3 text-xs font-bold text-indigo-700">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="rounded-lg border border-indigo-200 px-3 py-2"
        >
          История
        </button>
        {user?.role === "superadmin" && (
          <button
            type="button"
            onClick={() => setEditing(!editing)}
            className="rounded-lg border border-slate-200 px-3 py-2"
          >
            {editing ? "Отмена" : "Исправить паспорт"}
          </button>
        )}
      </div>
      {editing && (
        <div className="space-y-3 rounded-lg bg-slate-50 p-3">
          {!!types.data?.length && (
            <SearchableSelect
              label="Тип оборудования"
              value={form.equipment_id}
              options={types.data}
              onChange={(equipment_id) => setForm({ ...form, equipment_id })}
            />
          )}
          <EditableField
            label="Заводской номер"
            maxLength={255}
            value={form.serial_number}
            isEditing
            onChange={(serial_number) => setForm({ ...form, serial_number })}
          />
          <EditableField
            label="Дата изготовления"
            maxLength={100}
            value={form.manufacture_date_text}
            isEditing
            onChange={(manufacture_date_text) => {
              if (isValidManufactureDate(manufacture_date_text))
                setForm({ ...form, manufacture_date_text });
            }}
          />
          <EditableField
            label="Причина исправления"
            maxLength={2000}
            type="textarea"
            value={form.reason}
            isEditing
            onChange={(reason) => setForm({ ...form, reason })}
          />
          {save.isError && (
            <p role="alert" className="text-xs text-red-700">
              {formatApiError(save.error, "Не удалось сохранить исправление")}
            </p>
          )}
          <button
            type="button"
            disabled={!form.reason.trim() || save.isPending}
            onClick={() => save.mutate()}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-bold text-white disabled:cursor-wait disabled:opacity-70"
          >
            {save.isPending && (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            )}
            {save.isPending ? "Сохранение…" : "Сохранить исправление"}
          </button>
        </div>
      )}
      {open &&
        createPortal(
          <dialog
            ref={dialogRef}
            aria-labelledby={historyTitleId}
            onCancel={(event) => {
              event.preventDefault();
              closeHistory();
            }}
            onClick={(event) => {
              if (event.target === event.currentTarget) closeHistory();
            }}
            className="m-auto w-[calc(100%-2rem)] max-w-6xl overflow-hidden rounded-2xl border border-slate-200 bg-white p-0 text-slate-900 shadow-2xl backdrop:bg-slate-900/60 backdrop:backdrop-blur-sm"
          >
            <div className="flex max-h-[85dvh] flex-col">
              <div className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-200 bg-slate-50 px-5 py-4">
                <div className="min-w-0">
                  <h2 id={historyTitleId} className="text-lg font-bold">
                    История изменений
                  </h2>
                  <p className="mt-1 text-sm text-black">
                    {node.tree_name || node.full_name} · №{" "}
                    {node.serial_number || "—"}
                  </p>
                </div>
                <button
                  type="button"
                  autoFocus
                  aria-label="Закрыть историю"
                  onClick={closeHistory}
                  className="shrink-0 rounded-lg p-2 text-slate-500 hover:bg-slate-200 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-indigo-500"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="min-h-0 overflow-auto overscroll-contain">
                {history.isLoading ? (
                  <p role="status" className="p-6 text-sm text-slate-600">
                    Загрузка истории…
                  </p>
                ) : history.isError ? (
                  <p role="alert" className="p-6 text-sm text-red-700">
                    Не удалось загрузить историю{" "}
                    <button
                      type="button"
                      className="underline"
                      onClick={() => history.refetch()}
                    >
                      Повторить
                    </button>
                  </p>
                ) : !history.data?.length ? (
                  <p className="p-6 text-sm text-slate-600">
                    Изменений не было
                  </p>
                ) : (
                  <table className="w-full min-w-[920px] table-fixed text-center text-sm [&_td]:align-middle [&_th]:align-middle">
                    <thead className="sticky top-0 z-10 bg-slate-100 text-xs font-bold text-slate-600">
                      <tr>
                        <th scope="col" className="w-[13%] px-4 py-3">
                          Дата изменения
                        </th>
                        <th scope="col" className="w-[15%] px-4 py-3">
                          Основание
                        </th>
                        <th scope="col" className="w-[18%] px-4 py-3">
                          До изменения
                        </th>
                        <th scope="col" className="w-[18%] px-4 py-3">
                          После изменения
                        </th>
                        <th scope="col" className="w-[21%] px-4 py-3">
                          Неисправность / причина
                        </th>
                        <th scope="col" className="w-[15%] px-4 py-3">
                          Автор
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {history.data.map((event) => (
                        <HistoryRow key={event.id} event={event} />
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </dialog>,
          document.body,
        )}
    </div>
  );
}

/** Показывает одно изменение позиции отдельной строкой истории */
function HistoryRow({ event }) {
  const restored = event.kind === "historical_replacement";
  const manual = event.kind === "manual_correction";
  const dateLabel = restored
    ? event.case_snapshot?.date_label || "Дата неизвестна"
    : manual
      ? new Date(event.recorded_at).toLocaleString("ru-RU")
      : formatDate(event.date);
  const reason = manual
    ? "Ручное исправление"
    : restored
      ? "Восстановленная замена"
      : `Случай №${event.display_number ?? event.case_snapshot?.display_number ?? "—"}`;
  const author = manual
    ? event.actor_name
    : restored
      ? "Восстановлено по комментариям к сверке"
      : event.case_snapshot?.creator_name;

  return (
    <tr className="even:bg-slate-100/70">
      <td className="px-4 py-4 font-semibold">{dateLabel}</td>
      <td className="px-4 py-4 font-semibold text-indigo-700">{reason}</td>
      <td className="relative px-10 py-4">
        <HistoryEquipment state={event.before} />
        <svg
          aria-hidden="true"
          viewBox="0 0 32 20"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
    className="absolute top-1/2 right-0 h-5 w-8 translate-x-1/2 -translate-y-1/2 text-black"
        >
          <path d="M3 10h26m-6-6 6 6-6 6" />
        </svg>
      </td>
      <td className="px-4 py-4">
        <HistoryEquipment state={event.after} />
      </td>
      <td className="space-y-1 px-4 py-4 break-words whitespace-pre-wrap">
        {event.case_snapshot?.malfunction && (
          <p>{event.case_snapshot.malfunction}</p>
        )}
        {event.reason && <p>{event.reason}</p>}
        {!event.reason && !event.case_snapshot?.malfunction && "—"}
      </td>
      <td
        className="px-4 py-4 break-words"
        title={restored ? undefined : author}
      >
        {restored ? author : author ? formatFullName(author) : "Не указан"}
      </td>
    </tr>
  );
}

/** Показывает номер и дату экземпляра до или после изменения */
function HistoryEquipment({ state }) {
  return (
    <div className="space-y-1 break-words">
      <p>{state.equipment_name?.replaceAll("_", " ") || "—"}</p>
      <p className="font-bold">№ {state.serial_number || "—"}</p>
      {state.manufacture_date_text && (
        <p className="text-slate-600">({state.manufacture_date_text})</p>
      )}
    </div>
  );
}
