import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../../context/AuthContext";
import api from "../../api/api";
import { SearchableSelect } from "../inputs/index.jsx";
import { isValidManufactureDate } from "../../utils/validators";
import { formatDate } from "../../utils/formatters";

/** Показывает историю позиции и форму исправления паспорта */
export function PassportPositionHistory({ passportId, node }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    equipment_id: node.equipment_id,
    serial_number: node.serial_number || "",
    manufacture_date_text: node.manufacture_date || "",
    reason: "",
  });
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
          onClick={() => setOpen(!open)}
          className="rounded-lg border border-indigo-200 px-3 py-2"
        >
          {open ? "Скрыть историю" : "История"}
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
          <label className="block text-xs text-slate-600">
            Заводской номер
            <input
              maxLength={255}
              className="mt-1 w-full rounded border border-slate-200 p-2"
              value={form.serial_number}
              onChange={(e) =>
                setForm({ ...form, serial_number: e.target.value })
              }
            />
          </label>
          <label className="block text-xs text-slate-600">
            Дата изготовления
            <input
              maxLength={100}
              className="mt-1 w-full rounded border border-slate-200 p-2"
              value={form.manufacture_date_text}
              onChange={(e) => {
                if (isValidManufactureDate(e.target.value))
                  setForm({ ...form, manufacture_date_text: e.target.value });
              }}
            />
          </label>
          <label className="block text-xs text-slate-600">
            Причина исправления
            <textarea
              maxLength={2000}
              className="mt-1 w-full rounded border border-slate-200 p-2"
              value={form.reason}
              onChange={(e) => setForm({ ...form, reason: e.target.value })}
            />
          </label>
          {save.isError && (
            <p role="alert" className="text-xs text-red-700">
              {save.error.response?.data?.detail ||
                "Не удалось сохранить исправление"}
            </p>
          )}
          <button
            type="button"
            disabled={!form.reason.trim() || save.isPending}
            onClick={() => save.mutate()}
            className="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-bold text-white disabled:opacity-40"
          >
            Сохранить исправление
          </button>
        </div>
      )}
      {open && (
        <div className="space-y-3">
          {history.isLoading ? (
            <p className="text-xs text-slate-500">Загрузка истории…</p>
          ) : history.isError ? (
            <p role="alert" className="text-xs text-red-700">
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
            <p className="text-xs text-slate-500">Изменений не было</p>
          ) : (
            history.data.map((event) => (
              <article
                key={event.id}
                className="space-y-1 rounded-lg border border-slate-200 p-3 text-xs text-slate-700"
              >
                <p className="font-bold">
                  {formatDate(event.date)} ·{" "}
                  {event.kind === "manual_correction"
                    ? "Ручное исправление"
                    : `Случай №${event.display_number ?? event.case_snapshot?.display_number ?? "—"}`}
                </p>
                <p>
                  {event.before.equipment_name?.replaceAll("_", " ")} · №{" "}
                  {event.before.serial_number || "—"} →{" "}
                  {event.after.equipment_name?.replaceAll("_", " ")} · №{" "}
                  {event.after.serial_number || "—"}
                </p>
                {(event.before.manufacture_date_text ||
                  event.after.manufacture_date_text) && (
                  <p>
                    Дата изготовления:{" "}
                    {event.before.manufacture_date_text || "—"} →{" "}
                    {event.after.manufacture_date_text || "—"}
                  </p>
                )}
                <p>
                  {event.kind === "manual_correction"
                    ? event.actor_name
                    : event.case_snapshot?.creator_name}
                </p>
                {event.case_snapshot?.malfunction && (
                  <p>{event.case_snapshot.malfunction}</p>
                )}
                {event.reason && <p>{event.reason}</p>}
                {event.kind === "manual_correction" && (
                  <p className="text-slate-400">
                    {new Date(event.recorded_at).toLocaleString("ru-RU")}
                  </p>
                )}
              </article>
            ))
          )}
        </div>
      )}
    </div>
  );
}
