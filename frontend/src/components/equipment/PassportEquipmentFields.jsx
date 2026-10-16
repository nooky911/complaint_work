import { useEffect, useMemo } from "react";
import {
  EditableField,
  MultiSelectField,
  SearchableSelect,
} from "../inputs/index.jsx";
import { usePassportEquipment } from "../../hooks/usePassportEquipment";
import { isValidManufactureDate } from "../../utils/validators";
import { formatApiError, sortOptionsByName } from "../../utils/formatters";

/** Возвращает сообщение об ошибке загрузки паспортных позиций */
const errorText = (error) =>
  formatApiError(error, "Не удалось загрузить паспортные позиции");
/** Сравнивает выбранные данные паспорта */
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

/** Добавляет дату изготовления в скобках рядом с номером */
const passportOptionName = (option, state = option.state) =>
  `${option.name} (${state?.manufacture_date_text || "—"})`;

/** Выбор неисправных экземпляров паспорта по секциям */
export function PassportEquipmentSelector({ data, updateField, query }) {
  const links = data.passport_links || [];
  const required = useMemo(
    () => query.data?.required_roles || [],
    [query.data],
  );
  useEffect(() => {
    const status = query.isError
      ? "error"
      : query.isFetching
        ? "loading"
        : "ready";
    if (
      data._passport_status !== status ||
      !same(data._passport_required_roles, required)
    ) {
      updateField("_passport_status", status, {
        _passport_required_roles: required,
      });
    }
  }, [
    query.isError,
    query.isFetching,
    data._passport_status,
    data._passport_required_roles,
    required,
    updateField,
  ]);

  if (query.isError)
    return (
      <p role="alert" className="text-xs text-red-700">
        {errorText(query.error)}{" "}
        <button
          type="button"
          onClick={() => query.refetch()}
          className="underline"
        >
          Повторить
        </button>
      </p>
    );
  if (query.isFetching && !query.data)
    return (
      <p className="text-xs text-slate-500">Загрузка экземпляров паспорта…</p>
    );

  /** Обновляет выбранные экземпляры, количество и даты снятого оборудования */
  const changeSelection = (role, values) => {
    const options = query.data?.[role] || [];
    let next = links.filter((x) => x.role !== role);
    next = next.concat(
      values.map((id) => {
        const option = options.find((x) => x.id === id);
        const parent =
          role === "element"
            ? next.find(
                (x) =>
                  x.role === "component" &&
                  option.ancestor_ids?.includes(x.node_id),
              )
            : null;
        return {
          node_id: id,
          role,
          version: option.version,
          parent_node_id: parent?.node_id || null,
          state: option.state,
          context: option.context,
        };
      }),
    );
    if (role === "component") {
      const elementOptions = query.data?.element || [];
      next = next.filter(
        (x) =>
          x.role !== "element" ||
          !required.includes("component") ||
          values.some((id) =>
            elementOptions
              .find((o) => o.id === x.node_id)
              ?.ancestor_ids?.includes(id),
          ),
      );
      next = next.map((x) =>
        x.role !== "element"
          ? x
          : {
              ...x,
              parent_node_id:
                values.find((id) =>
                  elementOptions
                    .find((o) => o.id === x.node_id)
                    ?.ancestor_ids?.includes(id),
                ) || null,
            },
      );
    }
    const related = {};
    for (const r of ["component", "element"]) {
      const selected = next.filter((x) => x.role === r);
      if (
        !selected.length &&
        !required.includes(r) &&
        !links.some((x) => x.role === r)
      )
        continue;
      related[`${r}_quantity`] = selected.length;
      related[`${r}_serial_number_old`] = selected
        .map((x) => x.state?.serial_number || "б/н")
        .join(", ");
      related[`${r}_manufacture_date_old`] = selected
        .map((x) => x.state?.manufacture_date_text || "—")
        .join(", ");
    }
    if (!next.length) related.replacement_items = [];
    updateField("passport_links", next, related);
  };

  return (
    <div className="space-y-3">
      {required
        .filter((role) => role !== "element" || data.element_equipment_id)
        .map((role) => (
          <div
            key={role}
            className="space-y-2 rounded-lg border border-indigo-200 bg-indigo-50/40 p-3"
          >
            <div className="flex items-baseline justify-between gap-4">
              <p className="min-w-0 text-sm font-bold text-indigo-900">
                {role === "component"
                  ? "Неисправные компоненты"
                  : "Неисправные элементы"}{" "}
                согласно паспорту
              </p>
              <p className="flex shrink-0 items-baseline gap-2 text-sm font-bold text-indigo-900">
                Количество:
                <span className="rounded-md bg-indigo-100 px-2 text-base font-black text-indigo-700">
                  {links.filter((x) => x.role === role).length}
                </span>
              </p>
            </div>
            {[1, 2, 4, 0].map((section) => {
              const options = sortOptionsByName(
                (query.data?.[role] || []).filter(
                  (x) =>
                    x.context.section === section &&
                    (role !== "element" ||
                      !required.includes("component") ||
                      links.some(
                        (l) =>
                          l.role === "component" &&
                          x.ancestor_ids?.includes(l.node_id),
                      )),
                ),
              );
              if (!options.length) return null;
              const selected = options
                .map((option) =>
                  links.find((x) => x.role === role && x.node_id === option.id),
                )
                .filter(Boolean);
              return (
                <div key={section} className="space-y-2">
                  <MultiSelectField
                    label={
                      section
                        ? `Секция ${options[0].context.section_name}`
                        : "Общее оборудование"
                    }
                    options={options.map((o) => ({
                      ...o,
                      name: passportOptionName(o),
                    }))}
                    selectedValues={selected.map((x) => x.node_id)}
                    onChange={(values) =>
                      changeSelection(role, [
                        ...links
                          .filter(
                            (x) =>
                              x.role === role &&
                              !options.some((o) => o.id === x.node_id),
                          )
                          .map((x) => x.node_id),
                        ...values,
                      ])
                    }
                    allowClear
                    placeholder="Выберите заводские номера"
                  />
                  {selected.map((x) => (
                    <div
                      key={x.node_id}
                      className="text-xs font-bold text-slate-900"
                    >
                      {passportOptionName(
                        options.find((o) => o.id === x.node_id),
                        x.state,
                      )}
                    </div>
                  ))}
                </div>
              );
            })}
            {!(query.data?.[role] || []).length && (
              <p className="text-xs text-amber-800">
                В выбранной секции нет экземпляров этого типа.
              </p>
            )}
          </div>
        ))}
    </div>
  );
}

/** Заполнение установленного оборудования по рассчитанному составу замены */
export function PassportReplacementFields({ data, updateField }) {
  const query = usePassportEquipment(data, true);
  const plan = query.data;
  const values = useMemo(
    () => data.replacement_items || [],
    [data.replacement_items],
  );
  useEffect(() => {
    if (!plan || query.isFetching) return;
    const next = plan.map((row) => {
      const saved = values.find((x) => x.node_id === row.node_id);
      return {
        node_id: row.node_id,
        version: row.version,
        equipment_id: saved?.equipment_id ?? row.equipment_id,
        serial_number: saved?.serial_number ?? null,
        manufacture_date_text: saved?.manufacture_date_text ?? null,
      };
    });
    if (!same(next, values)) updateField("replacement_items", next);
  }, [plan, query.isFetching, values, updateField]);
  useEffect(() => {
    const invalid =
      query.isError ||
      query.isFetching ||
      !plan ||
      plan.some((row) => {
        const value = values.find((x) => x.node_id === row.node_id);
        return (
          !value ||
          (row.required_serial &&
            (!value.serial_number?.trim() ||
              ["б/н", "-", "—"].includes(
                value.serial_number.trim().toLowerCase(),
              ))) ||
          !isValidManufactureDate(value.manufacture_date_text)
        );
      });
    if (data._passport_replacement_invalid !== invalid)
      updateField("_passport_replacement_invalid", invalid);
  }, [
    query.isError,
    query.isFetching,
    plan,
    values,
    data._passport_replacement_invalid,
    updateField,
  ]);
  if (query.isError)
    return (
      <p role="alert" className="text-xs text-red-700">
        {errorText(query.error)}{" "}
        <button
          type="button"
          onClick={() => query.refetch()}
          className="underline"
        >
          Повторить
        </button>
      </p>
    );
  if (!plan)
    return (
      <p className="text-xs text-slate-500">Расчёт установленного состава…</p>
    );
  /** Обновляет поле установленного экземпляра */
  const change = (row, field, value) =>
    updateField(
      "replacement_items",
      values.map((x) =>
        x.node_id === row.node_id ? { ...x, [field]: value || null } : x,
      ),
    );
  return (
    <div className="space-y-3">
      {plan.some((r) => r.scope === "kmb") && (
        <p className="rounded-lg bg-amber-50 p-2 text-xs text-amber-900">
          Замена КМБ. Номера КП и ТЭД обязательны. Остальные номера и даты можно
          заполнить позже.
        </p>
      )}
      {plan.map((row, index) => {
        const value = values.find((x) => x.node_id === row.node_id) || row;
        const parentInPlan = plan.some((p) => p.node_id === row.parent_node_id);
        return (
          <div
            key={row.node_id}
            style={{ marginLeft: Math.min(row.depth || 0, 6) * 12 }}
            className={`space-y-2 rounded-lg border border-emerald-200 bg-white p-3 ${parentInPlan ? "border-l-4" : ""}`}
          >
            {(index === 0 || plan[index - 1].group_key !== row.group_key) && (
              <p className="text-sm font-bold text-emerald-800">
                Секция {row.context.section_name} ·{" "}
                {row.scope === "kmb"
                  ? `КМБ, КП${row.context.kp}`
                  : row.position}
              </p>
            )}
            <p className="text-sm font-bold text-slate-900">
              {row.label}
              {row.required_serial ? " *" : ""}
            </p>
            {row.allowed_types.length > 1 && (
              <SearchableSelect
                label="Установленный тип"
                options={row.allowed_types}
                value={value.equipment_id}
                onChange={(id) => change(row, "equipment_id", id)}
              />
            )}
            <div className="grid grid-cols-2 gap-3">
              <EditableField
                label="Заводской номер"
                isEditing
                maxLength={255}
                value={value.serial_number || ""}
                onChange={(serial) => change(row, "serial_number", serial)}
                placeholder={row.required_serial ? "Обязательно" : "Неизвестен"}
              />
              <EditableField
                label="Дата изготовления"
                isEditing
                maxLength={100}
                value={value.manufacture_date_text || ""}
                onChange={(date) => {
                  if (isValidManufactureDate(date))
                    change(row, "manufacture_date_text", date);
                }}
                placeholder="мм.гггг"
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** Показывает выбранные или установленные экземпляры в случае */
export function PassportInstanceSummary({ items = [], installed = false }) {
  if (!items.length) return null;
  return (
    <div className="space-y-2 rounded-lg border border-indigo-200 bg-white p-3">
      {items.map((item) => {
        const state = installed ? item : item.state;
        return (
          <div
            key={`${item.role || "installed"}-${item.node_id}`}
            className="text-xs text-slate-700"
          >
            <span className="font-bold">
              {item.context?.section_name} · {item.context?.caption}
            </span>{" "}
            — {state?.equipment_name?.replaceAll("_", " ")} · №{" "}
            {state?.serial_number || "—"} ·{" "}
            {state?.manufacture_date_text || "—"}
          </div>
        );
      })}
    </div>
  );
}
