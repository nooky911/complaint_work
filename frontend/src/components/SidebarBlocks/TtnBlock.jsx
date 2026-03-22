import { MultiSelectField } from "../inputs/index.jsx";
import { REPAIR_FIELDS_LABELS } from "../../constants/labels";
import { formatDate } from "../../utils/formatters";

export const TtnBlock = ({ filters, options, updateFilter }) => {
  const prepareDateOptions = (dateStrings) => {
    if (!dateStrings || !Array.isArray(dateStrings)) return [];
    return dateStrings.map((dateStr) => ({
      id: dateStr,
      name: formatDate(dateStr),
    }));
  };

  return (
    <>
      {/* 1. ТТН замены */}
      <div className="grid grid-cols-2 gap-3">
        <MultiSelectField
          label={"ТТН о замене"}
          selectedValues={filters.ttn_replacement}
          options={options?.ttn_replacement}
          onChange={(v) => updateFilter("ttn_replacement", v)}
          placeholder="№"
        />
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.ttn_replacement_date}
          selectedValues={filters.ttn_replacement_date}
          options={prepareDateOptions(options?.ttn_replacement_dates)}
          onChange={(v) => updateFilter("ttn_replacement_date", v)}
          placeholder="Выбрать"
        />
      </div>

      <div className="h-px w-full bg-slate-300/30" />

      {/* 2. ТТН с РЦ */}
      <div className="grid grid-cols-2 gap-3">
        <MultiSelectField
          label={"ТТН из РЦ"}
          selectedValues={filters.ttn_from_rc}
          options={options?.ttn_from_rc}
          onChange={(v) => updateFilter("ttn_from_rc", v)}
          placeholder="№"
        />
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.ttn_from_rc_date}
          selectedValues={filters.ttn_from_rc_date}
          options={prepareDateOptions(options?.ttn_from_rc_dates)}
          onChange={(v) => updateFilter("ttn_from_rc_date", v)}
          placeholder="Выбрать"
        />
      </div>

      <div className="h-px w-full bg-slate-300/30" />

      {/* 3. ТТН поставщику */}
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <MultiSelectField
            label={"ТТН поставщику"}
            selectedValues={filters.ttn_to_supplier}
            options={options?.ttn_to_supplier}
            onChange={(v) => updateFilter("ttn_to_supplier", v)}
            placeholder="№"
          />
          <MultiSelectField
            label={"Дата отгрузки"}
            selectedValues={filters.ttn_to_supplier_date}
            options={prepareDateOptions(options?.ttn_to_supplier_dates)}
            onChange={(v) => updateFilter("ttn_to_supplier_date", v)}
            placeholder="Выбрать"
          />
        </div>
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.ttn_to_supplier_provider}
          selectedValues={filters.to_supplier_provider_id}
          options={options?.shipping_providers?.slice(0, 5)}
          onChange={(v) => updateFilter("to_supplier_provider_id", v)}
          placeholder="Все перевозчики"
        />
      </div>

      <div className="h-px w-full bg-slate-300/30" />

      {/* 4. ТТН от поставщика */}
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <MultiSelectField
            label={"ТТН от поставщика"}
            selectedValues={filters.ttn_from_supplier}
            options={options?.ttn_from_supplier}
            onChange={(v) => updateFilter("ttn_from_supplier", v)}
            placeholder="№"
          />
          <MultiSelectField
            label={REPAIR_FIELDS_LABELS.ttn_from_supplier_date}
            selectedValues={filters.ttn_from_supplier_date}
            options={prepareDateOptions(options?.ttn_from_supplier_dates)}
            onChange={(v) => updateFilter("ttn_from_supplier_date", v)}
            placeholder="Выбрать"
          />
        </div>
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.ttn_from_supplier_provider}
          selectedValues={filters.from_supplier_provider_id}
          options={options?.from_shipping_providers?.slice(0, 5)}
          onChange={(v) => updateFilter("from_supplier_provider_id", v)}
          placeholder="Все перевозчики"
        />
      </div>
    </>
  );
};
