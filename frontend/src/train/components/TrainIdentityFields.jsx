import { REPAIR_FIELDS_LABELS, SHARED_LABELS } from "../../constants/labels";
import { formatWagonNumbers } from "../../utils/formatters";
import {
  DataField,
  SelectField,
  SearchableSelect,
  SectionSelect,
} from "../../components/inputs/index.jsx";

/** Показывает поездные модель, номер и выбор вагонов */
export function TrainIdentityFields({
  form,
  references: r,
  passport: query,
  validation,
  showError,
}) {
  const { data, editing } = form;
  const { passports, passport, selectModel, selectPassport, selectWagons } =
    query;
  return editing ? (
    <>
      <SelectField
        label={SHARED_LABELS.train_type}
        value={data.train.train_model_id}
        options={r.train_models}
        isEditing
        error={showError && validation.isLocoModelMissing}
        onChange={selectModel}
      />
      <SearchableSelect
        label={SHARED_LABELS.electric_train_number}
        value={data.passport_id}
        options={(passports.data || []).map((p) => ({
          id: p.id,
          name: p.number,
        }))}
        isDisabled={!data.train.train_model_id}
        placeholder={
          data.train.train_model_id
            ? "Выберите номер или найдите его"
            : "Сначала выберите тип поезда"
        }
        isLoading={passports.isFetching}
        loadError={passports.isError}
        onRetry={passports.refetch}
        error={showError && validation.isLocoNumberMissing}
        onChange={selectPassport}
      />
      <SectionSelect
        label={REPAIR_FIELDS_LABELS.wagon}
        isEditing
        options={(passport.data?.wagons || []).map((wagon) => ({
          ...wagon,
          name: formatWagonNumbers([wagon.name]),
        }))}
        selectedValues={data.train.wagon_node_ids}
        isDisabled={!data.passport_id || !passport.data}
        error={showError && validation.isSectionMissing}
        onChange={selectWagons}
      />
    </>
  ) : (
    <>
      <DataField
        label={SHARED_LABELS.train_type}
        value={
          r.train_models.find((m) => m.id === data.train.train_model_id)?.name
        }
      />
      <DataField
        label={SHARED_LABELS.electric_train_number}
        value={data.train.train_number}
      />
      <DataField
        label={REPAIR_FIELDS_LABELS.wagon}
        value={formatWagonNumbers(data.train.wagon_names)}
      />
    </>
  );
}
