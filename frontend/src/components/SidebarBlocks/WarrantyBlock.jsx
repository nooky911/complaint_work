import { MultiSelectField } from "../inputs/index.jsx";
import { REPAIR_FIELDS_LABELS } from "../../constants/labels";
import { formatDate } from "../../utils/formatters";

export const WarrantyBlock = ({ filters, options, updateFilter }) => {
  const prepareDateOptions = (dateStrings) => {
    if (!dateStrings || !Array.isArray(dateStrings)) return [];
    return dateStrings.map((dateStr) => ({
      id: dateStr,
      name: formatDate(dateStr),
    }));
  };

  return (
    <>
      {/* 1. Уведомление */}
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <MultiSelectField
            label="№ Ув-ия"
            selectedValues={filters.notification_number}
            options={options?.notification_numbers}
            onChange={(v) => updateFilter("notification_number", v)}
            placeholder="№"
          />
          <MultiSelectField
            label="Дата ув-ия"
            selectedValues={filters.notification_date}
            options={prepareDateOptions(options?.notification_dates)}
            onChange={(v) => updateFilter("notification_date", v)}
            placeholder="Выбрать"
          />
        </div>
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.summary}
          selectedValues={filters.notification_summary_id}
          options={options?.notification_summaries}
          onChange={(v) => updateFilter("notification_summary_id", v)}
          placeholder="Все варианты"
        />
      </div>

      <div className="h-px w-full bg-slate-300/30" />

      {/* 2. Повторное уведомление */}
      <div className="grid grid-cols-2 gap-3">
        <MultiSelectField
          label="№ повт. ув-ия"
          selectedValues={filters.re_notification_number}
          options={options?.re_notification_numbers}
          onChange={(v) => updateFilter("re_notification_number", v)}
          placeholder="№"
        />
        <MultiSelectField
          label="Дата повт."
          selectedValues={filters.re_notification_date}
          options={prepareDateOptions(options?.re_notification_dates)}
          onChange={(v) => updateFilter("re_notification_date", v)}
          placeholder="Выбрать"
        />
      </div>

      <div className="h-px w-full bg-slate-300/30" />

      {/* 3. Письмо-ответ */}
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <MultiSelectField
            label="№ Ответа"
            selectedValues={filters.response_letter_number}
            options={options?.response_letter_numbers}
            onChange={(v) => updateFilter("response_letter_number", v)}
            placeholder="№"
          />
          <MultiSelectField
            label="Дата ответа"
            selectedValues={filters.response_letter_date}
            options={prepareDateOptions(options?.response_letter_dates)}
            onChange={(v) => updateFilter("response_letter_date", v)}
            placeholder="Выбрать"
          />
        </div>
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.summary}
          selectedValues={filters.response_summary_id}
          options={options?.response_summaries}
          onChange={(v) => updateFilter("response_summary_id", v)}
          placeholder="Все варианты"
        />
      </div>

      <div className="h-px w-full bg-slate-300/30" />

      {/* 4. Акт РА (Рекламационный) */}
      <div className="grid grid-cols-2 gap-3">
        <MultiSelectField
          label="№ РА"
          selectedValues={filters.claim_act_number}
          options={options?.claim_act_numbers}
          onChange={(v) => updateFilter("claim_act_number", v)}
          placeholder="№"
        />
        <MultiSelectField
          label="Дата РА"
          selectedValues={filters.claim_act_date}
          options={prepareDateOptions(options?.claim_act_dates)}
          onChange={(v) => updateFilter("claim_act_date", v)}
          placeholder="Выбрать"
        />
      </div>

      <div className="h-px w-full bg-slate-300/30" />

      {/* 5. АВР и Решение */}
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <MultiSelectField
            label="№ АВР"
            selectedValues={filters.work_completion_act_number}
            options={options?.work_completion_act_numbers}
            onChange={(v) => updateFilter("work_completion_act_number", v)}
            placeholder="№"
          />
          <MultiSelectField
            label="Дата АВР"
            selectedValues={filters.work_completion_act_date}
            options={prepareDateOptions(options?.work_completion_act_dates)}
            onChange={(v) => updateFilter("work_completion_act_date", v)}
            placeholder="Выбрать"
          />
        </div>
        <MultiSelectField
          label={REPAIR_FIELDS_LABELS.summary}
          selectedValues={filters.decision_summary_id}
          options={options?.decision_summaries}
          onChange={(v) => updateFilter("decision_summary_id", v)}
          placeholder="Все решения"
        />
      </div>
    </>
  );
};
