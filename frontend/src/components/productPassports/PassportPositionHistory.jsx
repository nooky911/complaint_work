import { REPAIR_FIELDS_LABELS, SHARED_LABELS } from "../../constants/labels";
import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { PassportFiles } from "./PassportFiles";
import { Loader2, X } from "lucide-react";
import {
  useIsMutating,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useAuth } from "../../context/AuthContext";
import api from "../../api/api";
import { useProductPassport } from "../../hooks/api/index.jsx";
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
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
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
  const historyFiles = useQuery({
    queryKey: ["passport-files", passportId, node.id, "history"],
    queryFn: async ({ signal }) =>
      (
        await api.get(
          `/product-passports/${passportId}/nodes/${node.id}/file-history`,
          { signal },
        )
      ).data,
    enabled: open,
    staleTime: 30000,
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
        {canCorrectPassport(user, node.direction) && (
          <button
            type="button"
            onClick={() => setEditing(!editing)}
            className="rounded-lg border border-slate-200 px-3 py-2"
          >
            {editing ? "Отмена" : "Исправить паспорт"}
          </button>
        )}
      </div>
      <PassportFiles passportId={passportId} nodeId={node.id} />
      {editing && (
        <PassportCorrectionForm
          passportId={passportId}
          node={node}
          onSaved={() => setEditing(false)}
        />
      )}
      {open && (
        <PassportPositionDialog
          title="История изменений"
          node={node}
          wide
          onClose={() => setOpen(false)}
        >
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
            <p className="p-6 text-sm text-slate-600">Изменений не было</p>
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
                  <HistoryRow
                    key={event.id}
                    event={event}
                    passportId={passportId}
                    nodeId={node.id}
                    fileContexts={historyFiles.data?.[event.id]}
                    historyLoading={historyFiles.isLoading}
                    historyError={historyFiles.isError}
                    retryHistory={() => historyFiles.refetch()}
                  />
                ))}
              </tbody>
            </table>
          )}
        </PassportPositionDialog>
      )}
    </div>
  );
}

/** Проверяет право исправлять паспорт выбранного направления */
const canCorrectPassport = (user, direction) =>
  user?.role === "superadmin" ||
  (user?.role === "editor" && user.direction === (direction || "loco"));

/** Открывает форму исправления поверх карточки выбранного экземпляра */
export function PassportCorrectionButton({
  passportId,
  nodeId,
  direction,
  caseContext,
  onSaved,
}) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const passport = useProductPassport(open ? passportId : null, {
    refresh: true,
  });
  const saving =
    useIsMutating({
      mutationKey: ["passport-correction", passportId, nodeId],
    }) > 0;
  if (!canCorrectPassport(user, direction)) return null;
  const node = passport.data?.nodes.find((item) => item.id === nodeId);
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-indigo-700 hover:bg-indigo-50"
      >
        Исправить паспорт
      </button>
      {open && (
        <PassportPositionDialog
          title="Исправить паспорт"
          node={node}
          onClose={() => {
            if (!saving) setOpen(false);
          }}
        >
          <div className="space-y-3 p-5">
            {passport.isFetching ? (
              <p role="status" className="text-sm text-slate-600">
                Загрузка паспорта…
              </p>
            ) : node && !passport.isError ? (
              <PassportCorrectionForm
                passportId={passportId}
                node={node}
                caseContext={caseContext}
                onSaved={(result) => {
                  onSaved(result);
                  setOpen(false);
                }}
              />
            ) : (
              <p role="alert" className="text-sm text-red-700">
                Не удалось загрузить позицию паспорта
              </p>
            )}
          </div>
        </PassportPositionDialog>
      )}
    </>
  );
}

/** Показывает одно и то же исправление в паспорте и в форме случая */
function PassportCorrectionForm({ passportId, node, caseContext, onSaved }) {
  const queryClient = useQueryClient();
  const [keepScans, setKeepScans] = useState(true);
  const [version] = useState(node.version);
  const [initial] = useState({
    equipment_id: node.equipment_id,
    serial_number: node.serial_number || "",
    manufacture_date_text: node.manufacture_date || "",
    reason: "",
  });
  const [form, setForm] = useState(initial);
  const types = useQuery({
    queryKey: [
      "product-passports",
      passportId,
      node.id,
      "types",
      caseContext,
      caseContext && version,
    ],
    queryFn: async () =>
      (
        await api.get(
          `/product-passports/${passportId}/nodes/${node.id}/types`,
          {
            params: caseContext && {
              ...caseContext,
              expected_version: version,
            },
          },
        )
      ).data,
    ...(caseContext ? { staleTime: 0, retry: false } : {}),
  });
  const emptyValue = (value) =>
    ["", "б/н", "—", "-"].includes(
      String(value || "")
        .trim()
        .toLowerCase(),
    );
  const sameOrAdded = (before, after) =>
    emptyValue(before) || String(before).trim() === String(after || "").trim();
  const canKeepScans =
    sameOrAdded(node.serial_number, form.serial_number) &&
    sameOrAdded(node.manufacture_date, form.manufacture_date_text);
  const currentFiles = useQuery({
    queryKey: ["passport-files", passportId, node.id, "current"],
    queryFn: async ({ signal }) =>
      (
        await api.get(
          `/product-passports/${passportId}/nodes/${node.id}/files`,
          { signal },
        )
      ).data,
    enabled: !caseContext || types.isSuccess,
    staleTime: 30000,
  });
  const save = useMutation({
    mutationKey: ["passport-correction", passportId, node.id],
    mutationFn: () =>
      api.patch(`/product-passports/${passportId}/nodes/${node.id}`, {
        ...form,
        serial_number:
          form.serial_number === initial.serial_number
            ? undefined
            : form.serial_number,
        manufacture_date_text:
          form.manufacture_date_text === initial.manufacture_date_text
            ? undefined
            : form.manufacture_date_text,
        ...caseContext,
        preserve_existing_files: canKeepScans ? keepScans : undefined,
        expected_version: version,
      }),
    onSuccess: async ({ data }) => {
      onSaved(data);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["product-passports"] }),
        queryClient.invalidateQueries({
          queryKey: ["passport-files", passportId, node.id],
        }),
        ...(node.direction === "train"
          ? [
              queryClient.invalidateQueries({ queryKey: ["train-cases"] }),
              queryClient.invalidateQueries({
                queryKey: ["train-filter-options"],
              }),
              queryClient.invalidateQueries({
                queryKey: ["dynamicFilterOptions", "train"],
              }),
              queryClient.invalidateQueries({ queryKey: ["train-passport"] }),
              queryClient.invalidateQueries({
                queryKey: ["train-replacement-preview"],
              }),
            ]
          : [
              queryClient.invalidateQueries({ queryKey: ["case"] }),
              queryClient.invalidateQueries({ queryKey: ["cases"] }),
            ]),
      ]);
    },
  });
  return (
    <>
      {caseContext && types.isSuccess && !types.isFetching && (
        <PassportFiles
          passportId={passportId}
          nodeId={node.id}
          expectedVersion={version}
        />
      )}
      <div className="space-y-3 rounded-lg bg-slate-50 p-3">
        {types.isError && (
          <p role="alert" className="text-xs text-red-700">
            {formatApiError(
              types.error,
              "Не удалось проверить позицию паспорта",
            )}{" "}
            <button
              type="button"
              onClick={() => types.refetch()}
              className="underline"
            >
              Повторить
            </button>
          </p>
        )}
        {!!types.data?.length && (
          <SearchableSelect
            label={SHARED_LABELS.equipment_type}
            value={form.equipment_id}
            options={types.data}
            onChange={(equipment_id) => setForm({ ...form, equipment_id })}
          />
        )}
        <EditableField
          label={SHARED_LABELS.factory_number}
          maxLength={255}
          value={form.serial_number}
          isEditing
          onChange={(serial_number) => setForm({ ...form, serial_number })}
        />
        <EditableField
          label={REPAIR_FIELDS_LABELS.manufacture_date}
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
        {canKeepScans &&
          !!currentFiles.data?.files?.length &&
          form.equipment_id !== node.equipment_id && (
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={keepScans}
                onChange={(event) => setKeepScans(event.target.checked)}
              />
              Сохранить привязанные сканы паспорта
            </label>
          )}
        {save.isError && (
          <p role="alert" className="text-xs text-red-700">
            {formatApiError(save.error, "Не удалось сохранить исправление")}
          </p>
        )}
        <button
          type="button"
          disabled={
            !form.reason.trim() ||
            save.isPending ||
            types.isPending ||
            types.isError
          }
          onClick={() => save.mutate()}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-bold text-white disabled:cursor-wait disabled:opacity-70"
        >
          {save.isPending && (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          )}
          {save.isPending ? "Сохранение…" : "Сохранить исправление"}
        </button>
      </div>
    </>
  );
}

/** Удерживает фокус в окне позиции и возвращает его после закрытия */
function PassportPositionDialog({ title, node, wide, onClose, children }) {
  const dialogRef = useRef(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = dialogRef.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return createPortal(
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      className={`m-auto w-[calc(100%-2rem)] ${wide ? "max-w-6xl" : "max-w-md"} overflow-hidden rounded-2xl border border-slate-200 bg-white p-0 text-slate-900 shadow-2xl backdrop:bg-slate-900/60 backdrop:backdrop-blur-sm`}
    >
      <div className="flex max-h-[85dvh] flex-col">
        <div className="flex shrink-0 items-start justify-between gap-4 border-b border-slate-200 bg-slate-50 px-5 py-4">
          <div className="min-w-0">
            <h2 id={titleId} className="text-lg font-bold">
              {title}
            </h2>
            {node && (
              <p className="mt-1 text-sm text-black">
                {node.tree_name || node.full_name} · №{" "}
                {node.serial_number || "—"}
              </p>
            )}
          </div>
          <button
            type="button"
            autoFocus
            aria-label="Закрыть окно"
            onClick={onClose}
            className="shrink-0 rounded-lg p-2 text-slate-500 hover:bg-slate-200 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-indigo-500"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="min-h-0 overflow-auto overscroll-contain">
          {children}
        </div>
      </div>
    </dialog>,
    document.body,
  );
}

/** Показывает одно изменение позиции отдельной строкой истории */
function HistoryRow({
  event,
  passportId,
  nodeId,
  fileContexts,
  historyLoading,
  historyError,
  retryHistory,
}) {
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
        <PassportFiles
          passportId={passportId}
          nodeId={nodeId}
          eventId={event.id}
          side="before"
          context={fileContexts?.before}
          compact
          historyLoading={historyLoading}
          historyError={historyError}
          retryHistory={retryHistory}
        />
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
        <PassportFiles
          passportId={passportId}
          nodeId={nodeId}
          eventId={event.id}
          side="after"
          context={fileContexts?.after}
          compact
          historyLoading={historyLoading}
          historyError={historyError}
          retryHistory={retryHistory}
        />
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
