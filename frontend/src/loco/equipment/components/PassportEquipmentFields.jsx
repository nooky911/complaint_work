import { replacementSerialLabel } from "../../../utils/formatters";
import { REPAIR_FIELDS_LABELS } from "../../../constants/labels";
import { Tooltip } from "../../../utils/Tooltip";
import { PassportCorrectionButton } from "../../../components/productPassports/PassportPositionHistory";
import { PassportSelectionGroup } from "../../../components/equipment/PassportSelectionGroup";
import { useEffect, useMemo } from "react";
import {
  DataField,
  EditableField,
  MultiSelectField,
  SearchableSelect,
} from "../../../components/inputs/index.jsx";
import { usePassportEquipment } from "../hooks/usePassportEquipment.js";
import { isValidManufactureDate } from "../../../utils/validators.js";
import {
  formatSerialNumber,
  formatToDB,
  formatApiError,
  sortOptionsByName,
} from "../../../utils/formatters.js";

/** Возвращает сообщение об ошибке загрузки паспортных позиций */
const errorText = (error) =>
  formatApiError(error, "Не удалось загрузить паспортные позиции");
/** Сравнивает выбранные данные паспорта */
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

/** Добавляет дату изготовления в скобках рядом с номером */
const passportOptionName = (option) =>
  `${option.name} (${option.state?.manufacture_date_text || "—"})`;

/** Выбор неисправных экземпляров паспорта по секциям */
export function PassportEquipmentSelector({ data, updateField, query }) {
  const links = data.passport_links || [];
  const singleComponent = links.filter((link) => link.role === "component").length === 1;
  const unavailable = !!query.data && links.some((link) =>
    !query.data[link.role]?.some((option) => option.id === link.node_id),
  );
  const required = useMemo(
    () => query.data?.required_roles || [],
    [query.data],
  );
  useEffect(() => {
    const status = query.isError || unavailable
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
    unavailable,
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
      options.filter((option) => values.includes(option.id)).map((option) => {
        const parent =
          role === "element"
            ? next.find(
                (x) =>
                  x.role === "component" &&
                  option.ancestor_ids?.includes(x.node_id),
              )
            : null;
        return {
          node_id: option.id,
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
      {unavailable && !query.isFetching && (
        <p role="alert" className="text-xs text-amber-800">
          Состав паспорта изменился. Выберите актуальный тип и экземпляр.
        </p>
      )}
      {required
        .filter((role) => role !== "element" || data.element_equipment_id)
        .map((role) => (
          <PassportSelectionGroup
            key={role}
            role={role}
            count={links.filter((x) => x.role === role).length}
          >
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
                  {role === "component" && singleComponent && selected.length === 1 && (
                    <div className="flex justify-end">
                      <PassportCorrectionButton
                        passportId={data.passport_id}
                        nodeId={selected[0].node_id}
                        direction="loco"
                        caseContext={{
                          case_id: data.id || null,
                          case_fault_date: formatToDB(data.fault_date) || null,
                          expected_case_revision: data.expected_revision || null,
                        }}
                        onSaved={(result) => {
                          if (result.case_revision != null) {
                            updateField("expected_revision", result.case_revision);
                          }
                          const option = result.position;
                          if (option?.equipment_id === data.component_equipment_id) {
                            updateField("passport_links", links.map((link) =>
                              link === selected[0]
                                ? { ...link, version: option.version, state: { ...link.state, ...option } }
                                : link,
                            ), data.id ? {} : {
                              component_serial_number_old: option.serial_number || "б/н",
                              component_manufacture_date_old: option.manufacture_date_text || "—",
                            });
                          }
                        }}
                      />
                    </div>
                  )}
                </div>
              );
            })}
            {!(query.data?.[role] || []).length && (
              <p className="text-xs text-amber-800">
                В выбранной секции нет экземпляров этого типа.
              </p>
            )}
          </PassportSelectionGroup>
        ))}
    </div>
  );
}

/** Заполнение установленного оборудования по рассчитанному составу замены */
export function PassportReplacementFields({ data, updateField }) {
  const query = usePassportEquipment(data, true);
  return <PassportReplacementRows data={data} updateField={updateField} query={query} />;
}

/** Показывает общий состав замены из локомотивного или поездного расчёта */
export function PassportReplacementRows({ data, updateField, query }) {
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
        equipment_id: saved && (saved.equipment_id === row.equipment_id || row.allowed_types.some((type) => type.id === saved.equipment_id))
          ? saved.equipment_id : row.equipment_id,
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
                {data.direction === "train" ? "" : "Секция "}{row.context.section_name} ·{" "}
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
                label={replacementSerialLabel(
                  data?.repair_type_id || data?.repair_type?.id,
                  row.role === "element",
                )}
                isEditing
                maxLength={255}
                value={value.serial_number || ""}
                onChange={(serial) => change(row, "serial_number", serial)}
                placeholder={row.required_serial ? "Обязательно" : "Неизвестен"}
              />
              <EditableField
                label={REPAIR_FIELDS_LABELS.manufacture_date}
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
export function PassportInstanceSummary({
  items = [],
  installed = false,
  equipmentReplacement = false,
  groupLabel = "Секция",
}) {
  // При просмотре замены КМБ оставляем только колёсную пару и тяговый двигатель
  const visibleItems = items.filter((item) => {
    if (!installed || item.scope !== "kmb") return true;
    const name =
      item.tree_name || item.context?.path?.split(" / ").at(-1) || "";
    return /кол[её]сная\s+пара|тяговый\s+(?:электро)?двигатель|(?:электро)?двигатель\s+тяговый/i.test(
      name,
    );
  });
  if (!visibleItems.length) return null;
  const sections = new Map();
  for (const item of visibleItems) {
    const section = item.context?.section_name || "—";
    const key = item.context?.section ?? section;
    if (!sections.has(key)) sections.set(key, { name: section, items: [] });
    sections.get(key).items.push(item);
  }
  return (
    <div className="space-y-4">
      {[...sections].map(([key, section]) => (
        <div
          key={key}
          className="grid grid-cols-1 gap-4 border-b-2 border-slate-300 pb-4 last:border-b-0 last:pb-0 sm:grid-cols-[max-content_minmax(0,1fr)]"
        >
          <div className="flex flex-col justify-center">
            <div className="grid w-max">
              <span
                aria-hidden="true"
                className="invisible col-start-1 row-start-1 border border-transparent px-3 text-sm font-medium"
              >
                {groupLabel === "Вагон" ? "Вагон" : "Бустер"}
              </span>
              <div className="col-start-1 row-start-1 [&_label]:ml-0 [&_label]:text-center [&_span]:text-center">
                <DataField label={groupLabel} value={section.name} />
              </div>
            </div>
          </div>
          <div className="min-w-0 space-y-3">
            {[...section.items]
              .sort(
                (a, b) =>
                  Number(a.role === "element") - Number(b.role === "element"),
              )
              .map((item) => {
                const element = item.role === "element";
                const state = installed ? item : item.state;
                const caption = item.context?.caption;
                const name = state?.equipment_name?.replaceAll("_", " ") || "—";
                return (
                  <div
                    key={`${item.role || "installed"}-${item.node_id}`}
                    className="grid grid-cols-1 gap-4 sm:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)_minmax(0,1fr)] sm:items-end"
                  >
                    <Tooltip
                      overflowOnly
                      text={`${name}${caption && caption !== "Позиция" ? ` · ${caption}` : ""}`}
                    >
                      <DataField
                        label={element ? "Элемент" : "Компонент"}
                        value={`${name}${caption && caption !== "Позиция" ? ` · ${caption}` : ""}`}
                      />
                    </Tooltip>
                    <Tooltip
                      overflowOnly
                      text={formatSerialNumber(state?.serial_number)}
                    >
                      <DataField
                        label={replacementSerialLabel(
                          equipmentReplacement ? 1 : 2,
                          element,
                        )}
                        value={formatSerialNumber(state?.serial_number)}
                      />
                    </Tooltip>
                    <DataField
                      label={REPAIR_FIELDS_LABELS.manufacture_date}
                      value={state?.manufacture_date_text}
                    />
                  </div>
                );
              })}
          </div>
        </div>
      ))}
    </div>
  );
}
