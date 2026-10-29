import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Plus,
  Pencil,
  X,
  KeyRound,
  LoaderCircle,
} from "lucide-react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/api";

const roles = {
  viewer: "Просмотр",
  editor: "Редактирование",
  superadmin: "Администратор",
};
const blank = {
  login: "",
  full_name: "",
  role: "viewer",
  is_active: true,
  partner_ids: [],
  restricted_access: false,
  allowed_rc_names: [],
};
/** Возвращает понятное сообщение об ошибке административного действия */
const errorText = (e) => {
  const d = e.response?.data?.detail;
  return typeof d === "string"
    ? d
    : Array.isArray(d)
      ? d.map((x) => x.msg).join("; ")
      : "Не удалось выполнить действие. Повторите попытку.";
};

/** Управляет пользователями и их взаимным доступом */
export default function AdminUsersPage() {
  const { user, login: refreshProfile } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(blank);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reset, setReset] = useState(false);
  const usersQuery = useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => (await api.get("/users/admin")).data,
    enabled: user?.role === "superadmin",
    staleTime: 0,
  });
  const users = usersQuery.data || [];
  if (user?.role !== "superadmin") return <Navigate to="/dashboard" replace />;
  const filtered = users.filter(
    (u) =>
      `${u.full_name} ${u.login}`
        .toLocaleLowerCase("ru")
        .includes(search.toLocaleLowerCase("ru")) &&
      (status === "all" || u.is_active === (status === "active")),
  );
  /** Открывает форму создания или редактирования пользователя */
  const open = (u) => {
    setEditing(u || { id: null });
    setForm(
      u
        ? {
            login: u.login,
            full_name: u.full_name || "",
            role: u.role,
            is_active: u.is_active,
            partner_ids: [...u.partner_ids],
            restricted_access: u.restricted_access || false,
            allowed_rc_names: u.allowed_rc_names || [],
          }
        : { ...blank, partner_ids: [] },
    );
    setError("");
    setNotice("");
    setReset(false);
  };
  /** Обновляет список пользователей и текущие права */
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    await queryClient.invalidateQueries({ queryKey: ["users"] });
    await refreshProfile();
  };
  /** Сохраняет пользователя и взаимный доступ */
  const save = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        ...form,
        login: form.login.trim(),
        full_name: form.full_name.trim(),
      };
      const response = editing.id
        ? await api.put(`/users/admin/${editing.id}`, payload)
        : await api.post("/users/admin", payload);
      setNotice(
        editing.id
          ? "Пользователь сохранён. Взаимный доступ обновлён у обоих участников."
          : `Пользователь создан. Пароль: ${response.data.password}. Пользователь сможет сменить его через меню профиля.`,
      );
      setEditing(null);
      await invalidate();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setSaving(false);
    }
  };
  /** Сбрасывает пароль и завершает предыдущие сессии */
  const resetPassword = async () => {
    setSaving(true);
    setError("");
    try {
      const { data } = await api.post(
        `/users/admin/${editing.id}/reset-password`,
      );
      setNotice(
        `Пароль пользователя ${editing.login} сброшен: ${data.password}. Предыдущие сессии завершены.`,
      );
      setReset(false);
      setEditing(null);
      await invalidate();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setSaving(false);
    }
  };
  const input =
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-black focus:border-indigo-500 focus:outline-none";
  return (
    <section className="flex min-h-0 flex-1 flex-col gap-4 overflow-auto bg-slate-50 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            aria-label="К списку случаев"
            className="rounded-lg border border-slate-200 bg-white p-2"
          >
            <ArrowLeft size={19} />
          </button>
          <h1 className="text-2xl font-bold text-slate-900">
            Админ-панель · Пользователи
          </h1>
        </div>
        <button
          type="button"
          onClick={() => open(null)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          <Plus size={16} />
          Добавить пользователя
        </button>
      </div>
      {notice && (
        <div
          role="status"
          className="flex items-start justify-between gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-emerald-900"
        >
          <span>{notice}</span>
          <button aria-label="Закрыть сообщение" onClick={() => setNotice("")}>
            <X size={18} />
          </button>
        </div>
      )}
      <div className="flex flex-wrap gap-3">
        <input
          aria-label="Поиск по ФИО или логину"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск по ФИО или логину"
          className={`${input} max-w-md`}
        />
        <select
          aria-label="Активность пользователей"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className={`${input} max-w-52`}
        >
          <option value="all">Все пользователи</option>
          <option value="active">Активные</option>
          <option value="inactive">Неактивные</option>
        </select>
      </div>
      {usersQuery.isPending ? (
        <p role="status">Загрузка пользователей…</p>
      ) : usersQuery.isError ? (
        <div role="alert" className="text-red-700">
          {errorText(usersQuery.error)}{" "}
          <button className="underline" onClick={() => usersQuery.refetch()}>
            Повторить
          </button>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-center text-sm">
            <thead className="bg-slate-100 text-slate-700">
              <tr>
                {[
                  "ФИО",
                  "Логин",
                  "Роль",
                  "Активность",
                  "Взаимный доступ",
                  "",
                ].map((h, i) => (
                  <th key={i} className="px-4 py-3 font-bold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr
                  key={u.id}
                  className="border-t border-slate-200 even:bg-slate-50"
                >
                  <td className="px-4 py-3 font-semibold text-black">
                    {u.full_name}
                  </td>
                  <td className="px-4 py-3">{u.login}</td>
                  <td className="px-4 py-3">{roles[u.role] || u.role}</td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        u.is_active
                          ? "font-medium text-emerald-700"
                          : "text-slate-500"
                      }
                    >
                      {u.is_active ? "Активен" : "Неактивен"}
                    </span>
                  </td>
                  <td className="max-w-sm px-4 py-3">
                    {u.partner_ids
                      .map(
                        (id) =>
                          users.find((p) => p.id === id)?.full_name ||
                          `Пользователь ${id}`,
                      )
                      .join(", ") || "—"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={() => open(u)}
                      className="mx-auto flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 font-semibold text-indigo-700"
                    >
                      <Pencil size={15} />
                      Редактировать
                    </button>
                  </td>
                </tr>
              ))}
              {!filtered.length && (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-slate-500">
                    Пользователи не найдены
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {editing && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="admin-user-title"
        >
          <form
            onSubmit={save}
            className="flex max-h-[90vh] w-full max-w-xl flex-col overflow-hidden rounded-xl bg-white shadow-xl"
          >
            <div className="flex items-center justify-between border-b border-slate-200 p-5">
              <h2 id="admin-user-title" className="text-lg font-bold">
                {editing.id
                  ? "Редактировать пользователя"
                  : "Добавить пользователя"}
              </h2>
              <button
                type="button"
                disabled={saving}
                onClick={() => setEditing(null)}
                aria-label="Закрыть"
              >
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4 overflow-auto p-5">
              {error && (
                <p
                  role="alert"
                  className="rounded-lg bg-red-50 p-3 text-sm text-red-700"
                >
                  {error}
                </p>
              )}
              <label className="block space-y-1 text-sm font-semibold">
                Полное ФИО
                <input
                  required
                  maxLength={255}
                  value={form.full_name}
                  onChange={(e) =>
                    setForm({ ...form, full_name: e.target.value })
                  }
                  className={input}
                />
              </label>
              <label className="block space-y-1 text-sm font-semibold">
                Логин
                <input
                  required
                  maxLength={50}
                  pattern="[A-Za-z0-9_.@-]+"
                  title="Латинские буквы, цифры и символы _ . @ -"
                  autoComplete="off"
                  value={form.login}
                  onChange={(e) => setForm({ ...form, login: e.target.value })}
                  className={input}
                />
              </label>
              <label className="block space-y-1 text-sm font-semibold">
                Роль
                <select
                  value={form.role}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      role: e.target.value,
                      restricted_access:
                        e.target.value === "viewer" && form.restricted_access,
                      allowed_rc_names:
                        e.target.value === "viewer"
                          ? form.allowed_rc_names
                          : [],
                      partner_ids:
                        e.target.value === "editor" ? form.partner_ids : [],
                    })
                  }
                  className={input}
                >
                  {Object.entries(roles).map(([v, label]) => (
                    <option key={v} value={v}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) =>
                    setForm({ ...form, is_active: e.target.checked })
                  }
                />
                Активный пользователь
              </label>
              <div className="space-y-3 rounded-lg border border-slate-200 p-3">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    disabled={form.role !== "viewer"}
                    checked={form.restricted_access}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        restricted_access: e.target.checked,
                        allowed_rc_names: e.target.checked
                          ? form.allowed_rc_names.length
                            ? form.allowed_rc_names
                            : ["13", "14", "15", "21"]
                          : [],
                      })
                    }
                  />
                  Ограниченный доступ (для роли «Просмотр»)
                </label>
                {form.restricted_access && (
                  <label className="block text-sm">
                    Разрешённые РЦ через запятую
                    <input
                      required
                      className={input}
                      value={form.allowed_rc_names.join(",")}
                      onChange={(e) =>
                        setForm({
                          ...form,
                          allowed_rc_names: e.target.value.split(","),
                        })
                      }
                      placeholder="13,14,15,21"
                    />
                  </label>
                )}
              </div>
              <fieldset
                disabled={form.role !== "editor"}
                className="rounded-lg border border-slate-200 p-3 disabled:opacity-60"
              >
                <legend className="px-1 text-sm font-bold">
                  Взаимное редактирование случаев
                </legend>
                <p className="mb-2 text-xs text-slate-600">
                  Выбранные пользователи смогут редактировать случаи друг друга.
                  Право действует для роли «Редактирование». Администратору
                  доступны все случаи.
                </p>
                <div className="max-h-44 space-y-2 overflow-auto">
                  {users
                    .filter((u) => u.id !== editing.id)
                    .map((u) => (
                      <label
                        key={u.id}
                        className="flex items-center gap-2 text-sm"
                      >
                        <input
                          type="checkbox"
                          checked={form.partner_ids.includes(u.id)}
                          className="m-0 shrink-0"
                          disabled={
                            u.role !== "editor" &&
                            !form.partner_ids.includes(u.id)
                          }
                          onChange={(e) =>
                            setForm({
                              ...form,
                              partner_ids: e.target.checked
                                ? [...form.partner_ids, u.id]
                                : form.partner_ids.filter((id) => id !== u.id),
                            })
                          }
                        />
                        <span>
                          {u.full_name}{" "}
                          <span className="text-xs text-slate-500">
                            ({u.login}, {roles[u.role]}
                            {u.is_active ? "" : ", неактивен"})
                          </span>
                        </span>
                      </label>
                    ))}
                  {users.length === 1 && editing.id && (
                    <p className="text-sm text-slate-500">
                      Других пользователей пока нет
                    </p>
                  )}
                </div>
              </fieldset>
              {!editing.id && (
                <p className="rounded-lg bg-slate-50 p-3 text-sm">
                  Начальный пароль будет показан после создания. Пользователь
                  сможет изменить его через меню профиля.
                </p>
              )}
              {editing.id && (
                <div className="pt-1">
                  {reset ? (
                    <div className="space-y-2 rounded-lg bg-amber-50 p-3 text-sm">
                      <p>
                        Сбросить пароль на начальный из настроек приложения?
                        Действующие сессии пользователя будут завершены.
                        Несохранённые изменения этой формы не применятся.
                      </p>
                      <div className="flex gap-3">
                        <button
                          type="button"
                          disabled={saving}
                          onClick={resetPassword}
                          className="font-bold text-red-700"
                        >
                          Подтвердить сброс
                        </button>
                        <button
                          type="button"
                          disabled={saving}
                          onClick={() => setReset(false)}
                        >
                          Отмена
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setReset(true)}
                      className="flex items-center gap-2 text-sm font-semibold text-red-700"
                    >
                      <KeyRound size={16} />
                      Сбросить пароль
                    </button>
                  )}
                </div>
              )}
            </div>
            <div className="flex justify-end gap-3 border-t border-slate-200 p-4">
              <button
                type="button"
                disabled={saving}
                onClick={() => setEditing(null)}
                className="rounded-lg border border-slate-300 px-4 py-2"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={saving || reset}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 font-semibold text-white disabled:opacity-60"
              >
                {saving && <LoaderCircle size={17} className="animate-spin" />}
                {saving ? "Сохранение…" : "Сохранить"}
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
