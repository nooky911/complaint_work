import { SectionPageHeader } from "../components/shared/SectionPageHeader";
import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Box,
  ChevronRight,
  ChevronDown,
  Search,
  Plus,
  Trash2,
  X,
  Pencil,
  Building2,
  CircleAlert,
  Copy,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/api";
import {
  EQUIPMENT_NAME_SPACE_ERROR,
  hasEquipmentNameSpaces,
} from "../utils/validators";
import { Tooltip } from "../utils/Tooltip";
import { MultiSelectField } from "../components/inputs/index.jsx";
import { SearchableSelect } from "../components/inputs/index.jsx";

const button =
  "inline-flex h-[38px] shrink-0 items-center justify-center gap-1.5 self-end whitespace-nowrap rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm font-semibold leading-none text-indigo-700 transition-colors hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-50";
const input =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-black";
const collator = new Intl.Collator("ru", { numeric: true });

/** Общий редактор дерева оборудования с раздельными правами направлений */
export default function EquipmentManagementPage({ direction = "loco" }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const client = useQueryClient();
  const allowed =
    user?.role === "superadmin" ||
    (user?.role === "editor" &&
      user?.direction === direction &&
      user?.can_manage_equipment);
  const [search, setSearch] = useState("");
  const [opened, setOpened] = useState(new Set());
  const [selected, setSelected] = useState(null);
  const [draft, setDraft] = useState({ name: "", supplier_id: "" });
  const [dialog, setDialog] = useState(null);
  const [newName, setNewName] = useState("");
  const [referenceSearch, setReferenceSearch] = useState("");
  const [copyTarget, setCopyTarget] = useState(null);
  const [copyFrom, setCopyFrom] = useState(null);
  const [faultIds, setFaultIds] = useState([]);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const base = `/catalog/${direction}`;
  const query = useQuery({
    queryKey: ["catalog-editor", direction],
    enabled: !!allowed,
    queryFn: async () => (await api.get(base)).data,
  });
  const data = query.data || {
    equipment: [],
    suppliers: [],
    malfunctions: [],
    links: [],
  };
  const byId = useMemo(
    () => new Map(data.equipment.map((item) => [item.id, item])),
    [data.equipment],
  );
  const visible = useMemo(() => {
    if (!search.trim()) return null;
    const ids = new Set();
    for (const item of data.equipment) {
      if (
        !item.name
          .replaceAll("_", " ")
          .toLocaleLowerCase()
          .includes(search.toLocaleLowerCase())
      )
        continue;
      let node = item;
      while (node && !ids.has(node.id)) {
        ids.add(node.id);
        node = byId.get(node.parent_id);
      }
    }
    return ids;
  }, [search, data.equipment, byId]);
  const path = (item) => {
    const names = [],
      seen = new Set();
    while (item && !seen.has(item.id)) {
      seen.add(item.id);
      names.unshift(item.name.replaceAll("_", " "));
      item = byId.get(item.parent_id);
    }
    return names.join(" / ");
  };
  const select = (item) => {
    setSelected(item.id);
    setFaultIds([]);
    setDraft({ name: item.name, supplier_id: item.supplier_id || "" });
    setError(null);
    setNotice("");
  };
  const run = async (action) => {
    if (busy) return;
    setBusy(true);
    setError(null);
    setNotice("");
    try {
      await action();
      await client.invalidateQueries();
      setNotice("Изменения сохранены");
    } catch (e) {
      const detail = e.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? { message: detail }
          : detail?.message
            ? detail
            : { message: "Не удалось сохранить изменения" },
      );
    } finally {
      setBusy(false);
    }
  };
  const startDialog = (value) => {
    setDialog(value);
    setNewName("");
    setReferenceSearch("");
    setError(null);
  };
  const item = byId.get(selected);
  const linked = new Set(
    data.links
      .filter((link) => link.equipment_id === selected)
      .map((link) => link.malfunction_id),
  );
  const renderTree = (parentId = null, depth = 0, ancestors = new Set()) =>
    data.equipment
      .filter(
        (entry) =>
          entry.parent_id === parentId && (!visible || visible.has(entry.id)),
      )
      .sort((a, b) => collator.compare(a.name, b.name))
      .map((entry) => {
        if (ancestors.has(entry.id)) return null;
        const children = data.equipment.some(
          (child) => child.parent_id === entry.id,
        );
        const expanded = visible || opened.has(entry.id);
        return (
          <div key={entry.id}>
            <div
              className={`flex items-center rounded-lg ${selected === entry.id ? "bg-indigo-100 text-indigo-900" : "hover:bg-slate-100"}`}
              style={{ paddingLeft: depth * 16 }}
            >
              <button
                type="button"
                aria-label={expanded ? "Свернуть" : "Раскрыть"}
                disabled={!children}
                className="p-1.5 disabled:invisible"
                onClick={() =>
                  setOpened((old) => {
                    const next = new Set(old);
                    if (next.has(entry.id)) next.delete(entry.id);
                    else next.add(entry.id);
                    return next;
                  })
                }
              >
                {expanded ? (
                  <ChevronDown size={16} />
                ) : (
                  <ChevronRight size={16} />
                )}
              </button>
              <button
                type="button"
                className="flex min-w-0 flex-1 items-center gap-2 py-2 pr-2 text-left text-sm font-semibold"
                onClick={() => select(entry)}
              >
                <Box size={18} className="shrink-0 text-blue-600" />
                <Tooltip overflowOnly text={entry.name.replaceAll("_", " ")}>
                  <span className="block truncate">
                    {entry.name.replaceAll("_", " ")}
                  </span>
                </Tooltip>
              </button>
            </div>
            {children &&
              expanded &&
              renderTree(
                entry.id,
                depth + 1,
                new Set([...ancestors, entry.id]),
              )}
          </div>
        );
      });
  if (!allowed)
    return (
      <div className="p-8 text-center">
        Нет разрешения на управление оборудованием этого раздела
      </div>
    );
  const referenceKind = dialog?.kind;
  const references = referenceKind ? data[referenceKind] || [] : [];
  return (
    <div className="flex h-full flex-col bg-slate-50 text-slate-900">
      <SectionPageHeader
        title={`Управление оборудованием · ${direction === "train" ? "Электропоезда" : "Локомотивы"}`}
        onBack={() => navigate(direction === "train" ? "/train" : "/dashboard")}
      >
        <button
          className={`${button} !text-xs !font-black tracking-wider uppercase`}
          onClick={() => startDialog({ kind: "suppliers" })}
        >
          <Building2 className="mr-2 inline" size={16} />
          Поставщики
        </button>
        <button
          className={`${button} !border-red-200 !bg-red-50 !text-xs !font-black tracking-wider !text-red-700 uppercase hover:!bg-red-100`}
          onClick={() => startDialog({ kind: "malfunctions" })}
        >
          <CircleAlert className="mr-2 inline" size={16} />
          Неисправности
        </button>
      </SectionPageHeader>
      <div className="grid min-h-0 flex-1 gap-4 overflow-auto p-5 lg:grid-cols-[minmax(280px,0.9fr)_minmax(0,1.6fr)]">
        <aside className="flex min-h-0 flex-col rounded-xl border border-gray-200 bg-white p-3">
          <div className="relative">
            <Search
              className="absolute top-2.5 left-3 text-slate-400"
              size={18}
            />
            <input
              className={`${input} pl-10`}
              placeholder="Поиск по всему классификатору"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="mt-3 flex-1 overflow-auto">
            {query.isPending ? (
              "Загрузка…"
            ) : query.error ? (
              <button onClick={() => query.refetch()}>
                Ошибка загрузки. Повторить
              </button>
            ) : (
              renderTree()
            )}
            {visible?.size === 0 && (
              <p className="p-3 text-sm">Ничего не найдено</p>
            )}
          </div>
          <button
            className={`${button} mt-3`}
            disabled={busy}
            onClick={() => startDialog({ equipment: true, parent: null })}
          >
            <Plus className="inline" size={16} /> Добавить корневую группу
          </button>
        </aside>
        <main className="min-w-0 rounded-xl border border-gray-200 bg-white p-5">
          {!item ? (
            <p className="py-12 text-center text-slate-500">
              Выберите оборудование в дереве или найдите по названию
            </p>
          ) : (
            <>
              <div className="flex flex-wrap items-start gap-3">
                <h2 className="min-w-0 flex-1 text-lg font-bold">
                  {item.name.replaceAll("_", " ")}
                </h2>
                <button
                  className={button}
                  onClick={() =>
                    startDialog({ equipment: true, parent: item.id })
                  }
                >
                  <Plus className="inline" size={16} /> Добавить дочернее
                </button>
              </div>
              <p className="mt-2 mb-5 text-sm text-slate-500">{path(item)}</p>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <label className="mb-4 block text-xs font-bold tracking-wider text-slate-500 uppercase [&_input]:mt-1 [&_input]:text-sm [&_input]:font-bold [&_input]:tracking-normal [&_input]:normal-case">
                  Наименование
                  <input
                    className={`${input} mt-1`}
                    aria-invalid={hasEquipmentNameSpaces(draft.name)}
                    value={draft.name}
                    onChange={(e) =>
                      setDraft({ ...draft, name: e.target.value })
                    }
                  />
                  {hasEquipmentNameSpaces(draft.name) && (
                    <span
                      role="alert"
                      className="mt-1 block text-xs font-normal tracking-normal text-red-600 normal-case"
                    >
                      {EQUIPMENT_NAME_SPACE_ERROR}
                    </span>
                  )}
                </label>
                <div>
                  <SearchableSelect
                    label="Поставщик"
                    placeholder="Найти поставщика…"
                    value={draft.supplier_id || null}
                    options={data.suppliers}
                    isDisabled={busy}
                    onChange={(value) =>
                      setDraft({ ...draft, supplier_id: value || "" })
                    }
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    Без явного поставщика используется поставщик родителя
                  </p>
                </div>
                {!draft.supplier_id && item.effective_supplier_id && (
                  <p className="mt-1 text-sm text-slate-500">
                    По иерархии:{" "}
                    {
                      data.suppliers.find(
                        (supplier) =>
                          supplier.id === item.effective_supplier_id,
                      )?.name
                    }
                  </p>
                )}
                <div className="mt-4 flex justify-end gap-2">
                  <button className={button} onClick={() => select(item)}>
                    Отмена
                  </button>
                  <button
                    disabled={
                      busy || !draft.name || hasEquipmentNameSpaces(draft.name)
                    }
                    className={`${button} !bg-blue-600 !text-white hover:!bg-blue-700`}
                    onClick={() =>
                      run(() =>
                        api.put(`${base}/equipment/${item.id}`, {
                          name: draft.name,
                          supplier_id: draft.supplier_id
                            ? Number(draft.supplier_id)
                            : null,
                        }),
                      )
                    }
                  >
                    {busy ? "Сохранение…" : "Сохранить"}
                  </button>
                </div>
              </div>
              <section className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <h3 className="mb-3 font-bold">Неисправности</h3>
                <div className="space-y-2">
                  {data.malfunctions
                    .filter((fault) => linked.has(fault.id))
                    .map((fault) => (
                      <div
                        key={fault.id}
                        className="flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-100 px-3 py-2 text-sm text-slate-900"
                      >
                        <span className="flex-1">{fault.name}</span>
                        <button
                          title="Отвязать от оборудования"
                          disabled={busy}
                          onClick={() =>
                            run(() =>
                              api.delete(
                                `${base}/equipment/${selected}/malfunctions/${fault.id}`,
                              ),
                            )
                          }
                        >
                          <X size={16} />
                        </button>
                      </div>
                    ))}
                </div>
                <div className="mt-3 space-y-3">
                  <fieldset
                    disabled={busy}
                    className={`min-w-0 ${busy ? "pointer-events-none opacity-60" : ""}`}
                  >
                    <MultiSelectField
                      label="Существующие неисправности"
                      placeholder="Найти и выбрать неисправности…"
                      selectedValues={faultIds}
                      options={data.malfunctions.filter(
                        (fault) => !linked.has(fault.id),
                      )}
                      onChange={setFaultIds}
                      allowClear
                    />
                  </fieldset>
                  <div className="flex flex-wrap justify-end gap-2">
                    <button
                      disabled={!faultIds.length || busy}
                      className={button}
                      onClick={() =>
                        run(async () => {
                          await api.post(
                            `${base}/equipment/${selected}/malfunctions`,
                            { malfunction_ids: faultIds },
                          );
                          setFaultIds([]);
                        })
                      }
                    >
                      Привязать
                    </button>
                    <button
                      className={button}
                      onClick={() =>
                        startDialog({
                          kind: "malfunctions",
                          attachTo: selected,
                        })
                      }
                    >
                      Создать и привязать
                    </button>
                    <button
                      disabled={busy}
                      className={`${button}`}
                      onClick={() => {
                        setCopyTarget(selected);
                        setCopyFrom(null);
                        setError(null);
                      }}
                    >
                      <Copy className="mr-1 inline" size={16} /> Взять с другого
                      оборудования
                    </button>
                  </div>
                </div>
              </section>
            </>
          )}
          {!dialog && error && <ErrorMessage error={error} />}
          {notice && (
            <p role="status" className="mt-4 text-sm text-green-700">
              {notice}
            </p>
          )}
        </main>
      </div>
      {copyTarget && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center bg-slate-900/40 p-5">
          <div className="w-full max-w-2xl rounded-xl border border-violet-100 bg-white p-5 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-bold text-violet-900">
                Привязать неисправности другого оборудования
              </h2>
              <button
                disabled={busy}
                onClick={() => {
                  setCopyTarget(null);
                  setError(null);
                }}
              >
                <X />
              </button>
            </div>
            <p className="mb-4 text-sm text-slate-600">
              Для: {byId.get(copyTarget)?.name.replaceAll("_", " ")}. Текущие
              неисправности сохранятся, повторные связи не добавятся.
            </p>
            <SearchableSelect
              label="Оборудование-источник"
              placeholder="Найти оборудование по названию или пути…"
              value={copyFrom}
              isDisabled={busy}
              onChange={setCopyFrom}
              options={data.equipment
                .filter(
                  (entry) =>
                    entry.id !== copyTarget &&
                    data.links.some((link) => link.equipment_id === entry.id),
                )
                .map((entry) => ({ id: entry.id, name: path(entry) }))}
            />
            {copyFrom && (
              <div className="mt-4 max-h-60 overflow-auto rounded-lg bg-violet-50 p-3 text-sm">
                <p className="mb-2 font-semibold">Неисправности источника:</p>
                {data.malfunctions
                  .filter((fault) =>
                    data.links.some(
                      (link) =>
                        link.equipment_id === copyFrom &&
                        link.malfunction_id === fault.id,
                    ),
                  )
                  .map((fault) => (
                    <p className="py-1" key={fault.id}>
                      {fault.name}
                      {data.links.some(
                        (link) =>
                          link.equipment_id === copyTarget &&
                          link.malfunction_id === fault.id,
                      )
                        ? " — уже привязана"
                        : ""}
                    </p>
                  ))}
              </div>
            )}
            {error && <ErrorMessage error={error} />}
            <div className="mt-4 flex justify-end gap-2">
              <button
                className={button}
                disabled={busy}
                onClick={() => {
                  setCopyTarget(null);
                  setError(null);
                }}
              >
                Отмена
              </button>
              <button
                className={`${button} !border-blue-600 !bg-blue-600 !text-white hover:!bg-blue-700`}
                disabled={!copyFrom || busy}
                onClick={() =>
                  run(async () => {
                    await api.post(
                      `${base}/equipment/${copyTarget}/copy-malfunctions`,
                      { source_equipment_id: copyFrom },
                    );
                    setCopyTarget(null);
                    setCopyFrom(null);
                  })
                }
              >
                {busy ? "Привязка…" : "Привязать все"}
              </button>
            </div>
          </div>
        </div>
      )}
      {dialog && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center bg-slate-900/40 p-5">
          <div className="max-h-[85vh] w-full max-w-2xl overflow-auto rounded-xl bg-white p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold">
                {dialog.equipment
                  ? "Добавить оборудование"
                  : referenceKind === "suppliers"
                    ? "Поставщики"
                    : "Неисправности"}
              </h2>
              <button disabled={busy} onClick={() => setDialog(null)}>
                <X />
              </button>
            </div>
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                run(async () => {
                  if (dialog.equipment) {
                    const response = await api.post(`${base}/equipment`, {
                      name: newName,
                      parent_id: dialog.parent,
                    });
                    setSelected(response.data.id);
                    setDraft({ name: newName, supplier_id: "" });
                    if (dialog.parent)
                      setOpened(new Set([...opened, dialog.parent]));
                    setDialog(null);
                  } else {
                    const response = await api.post(
                      `${base}/${referenceKind}`,
                      { name: newName },
                    );
                    if (dialog.attachTo) {
                      await api.put(
                        `${base}/equipment/${dialog.attachTo}/malfunctions/${response.data.id}`,
                      );
                      setDialog(null);
                    }
                  }
                  setNewName("");
                });
              }}
            >
              <input
                required
                className={input}
                placeholder="Название новой записи"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
              <button
                className={`${button}`}
                disabled={
                  busy ||
                  (!!dialog.equipment && hasEquipmentNameSpaces(newName))
                }
              >
                Добавить
              </button>
            </form>
            {dialog.equipment && hasEquipmentNameSpaces(newName) && (
              <p role="alert" className="mt-2 text-sm text-red-600">
                {EQUIPMENT_NAME_SPACE_ERROR}
              </p>
            )}
            {!dialog.equipment && (
              <>
                <input
                  className={`${input} mt-4`}
                  placeholder="Поиск в справочнике"
                  value={referenceSearch}
                  onChange={(e) => setReferenceSearch(e.target.value)}
                />
                <div className="mt-3 space-y-2">
                  {references
                    .filter((ref) =>
                      ref.name
                        .toLowerCase()
                        .includes(referenceSearch.toLowerCase()),
                    )
                    .map((ref) => (
                      <ReferenceRow
                        key={ref.id}
                        item={ref}
                        busy={busy}
                        canDelete={user.role === "superadmin"}
                        onSave={(name) =>
                          run(() =>
                            api.put(`${base}/${referenceKind}/${ref.id}`, {
                              name,
                            }),
                          )
                        }
                        onDelete={() =>
                          startDialog({ ...dialog, deleting: ref })
                        }
                      />
                    ))}
                </div>
              </>
            )}
            {dialog.deleting && (
              <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3">
                <p>Удалить «{dialog.deleting.name}» из общего справочника?</p>
                <div className="mt-2 flex gap-2">
                  <button
                    className={button}
                    disabled={busy}
                    onClick={() =>
                      run(async () => {
                        await api.delete(
                          `${base}/${referenceKind}/${dialog.deleting.id}`,
                        );
                        setDialog({ ...dialog, deleting: null });
                      })
                    }
                  >
                    Да, удалить
                  </button>
                  <button
                    className={button}
                    onClick={() => setDialog({ ...dialog, deleting: null })}
                  >
                    Отмена
                  </button>
                </div>
              </div>
            )}
            {error && <ErrorMessage error={error} />}
          </div>
        </div>
      )}
    </div>
  );
}

/** Редактирует имя справочной записи и предлагает подтверждение удаления */
function ReferenceRow({ item, busy, canDelete, onSave, onDelete }) {
  const [editing, setEditing] = useState(false),
    [name, setName] = useState(item.name);
  return (
    <div className="flex items-center gap-2 rounded-lg border border-gray-200 p-2">
      {editing ? (
        <>
          <input
            className={input}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button
            className={button}
            disabled={busy || !name.trim()}
            onClick={() => onSave(name)}
          >
            Сохранить
          </button>
          <button onClick={() => setEditing(false)}>
            <X size={16} />
          </button>
        </>
      ) : (
        <>
          <span className="flex-1 text-sm">{item.name}</span>
          <button
            title="Переименовать"
            onClick={() => {
              setName(item.name);
              setEditing(true);
            }}
          >
            <Pencil size={16} />
          </button>
          {canDelete && (
            <button
              title="Удалить из справочника"
              disabled={busy}
              onClick={onDelete}
            >
              <Trash2 size={16} className="text-red-600" />
            </button>
          )}
        </>
      )}
    </div>
  );
}

/** Показывает причину отказа и различимые номера случаев двух направлений */
function ErrorMessage({ error }) {
  return (
    <div
      role="alert"
      className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
    >
      <p>{error.message}</p>
      {error.cases?.length > 0 && (
        <ul className="mt-2 max-h-48 overflow-auto">
          {error.cases.map((item) => (
            <li key={`${item.direction}-${item.number}`}>
              {item.direction === "train" ? "Электропоезда" : "Локомотивы"} —
              случай №{item.number}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
