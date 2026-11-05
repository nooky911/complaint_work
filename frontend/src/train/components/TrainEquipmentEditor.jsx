import { PassportReplacementRows } from "../../loco/equipment/components/PassportEquipmentFields";
import { SHARED_LABELS } from "../../constants/labels";
import { PassportSelectionGroup } from "../../components/equipment/PassportSelectionGroup";
import { MultiSelectField } from "../../components/inputs/index.jsx";
import {
  EquipmentLevelSelector,
  EquipmentFields,
  EquipmentMalfunctionSelector,
} from "../../components/equipment/index.jsx";

/** Соединяет общий выбор оборудования с поездным паспортным адаптером */
export function TrainEquipmentEditor({
  form,
  equipment,
  references: r,
  validation,
  showError,
}) {
  const { data, editing, update } = form;
  const {
    selectedType,
    prettyEquipment,
    hierarchy,
    handleTrainSelection,
    leaf,
    roleNodes,
    allowedIds,
    classifierLoading,
    passportError,
    retryPassport,
    managedRoles,
    setInstances,
    levels,
  } = equipment;
  return (
    <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-200/50 p-3 shadow-sm">
      {!data.passport_id || !data.train.wagon_node_ids.length ? (
        <p className="text-xs text-slate-500">
          Выберите вагон для выбора оборудования из паспорта
        </p>
      ) : passportError ? (
        <p role="alert" className="text-xs text-red-700">
          Не удалось загрузить состав паспорта{" "}
          <button type="button" onClick={retryPassport} className="underline">
            Повторить
          </button>
        </p>
      ) : classifierLoading ? (
        <p className="text-xs text-slate-500">
          Загрузка оборудования выбранных вагонов…
        </p>
      ) : null}

      <div className="grid grid-cols-1 gap-3">
        <EquipmentLevelSelector
          index={0}
          label={SHARED_LABELS.equipment_type}
          value={selectedType}
          options={prettyEquipment.filter(
            (e) => e.level === 1 && allowedIds.has(e.id),
          )}
          isDisabled={classifierLoading}
          onChange={(value) =>
            hierarchy.handleLevelSelect(0, value, handleTrainSelection)
          }
        />
        {[
          ["Оборудование", "equipment_id", 2],
          ["Компонент", "component_id", 3],
          ["Элемент", "element_id", 4],
        ].map(([label, key, level]) => (
          <EquipmentLevelSelector
            key={key}
            index={level - 1}
            label={label}
            value={data.train[key]}
            error={
              showError &&
              validation?.isDesignationMissing &&
              (level === 2 ||
                (level === 3 && [2, 3].includes(Number(data.repair_type_id))))
            }
            options={hierarchy
              .getFilteredOptions([0, 1, 3, 4][level - 1])
              .filter((item) => allowedIds.has(item.id))}
            isDisabled={classifierLoading}
            onChange={(value) =>
              hierarchy.handleLevelSelect(
                [0, 1, 3, 4][level - 1],
                value,
                handleTrainSelection,
              )
            }
          />
        ))}
      </div>
      {!!leaf &&
        !classifierLoading &&
        managedRoles.map((role) => {
          const matchingNodes = roleNodes[role];
          const selectedIds = data.train.passport_node_ids.filter((id) =>
            matchingNodes.some((node) => node.id === id),
          );
          return (
            <PassportSelectionGroup
              key={role}
              role={role}
              count={selectedIds.length}
            >
              {[...new Set(matchingNodes.map((node) => node.wagon_id))].map(
                (wagonId) => {
                  const options = matchingNodes.filter(
                    (node) => node.wagon_id === wagonId,
                  );
                  const optionIds = new Set(options.map((node) => node.id));
                  return (
                    <div key={wagonId} className="space-y-2">
                      <MultiSelectField
                        label={
                          equipment.wagonNames.get(wagonId) || "Выбранный вагон"
                        }
                        selectedValues={selectedIds.filter((id) =>
                          optionIds.has(id),
                        )}
                        options={options.map((node) => ({
                          id: node.id,
                          name: `№ ${node.serial_number || "б/н"} (${node.manufacture_date || "—"})`,
                        }))}
                        onChange={(ids) =>
                          setInstances(
                            [
                              ...selectedIds.filter((id) => !optionIds.has(id)),
                              ...ids,
                            ],
                            role,
                          )
                        }
                        placeholder="Выберите заводские номера"
                        allowClear
                      />
                      {options
                        .filter((node) => selectedIds.includes(node.id))
                        .map((node) => (
                          <div
                            key={node.id}
                            className="text-xs font-bold text-slate-900"
                          >
                            № {node.serial_number || "б/н"} (
                            {node.manufacture_date || "—"})
                          </div>
                        ))}
                    </div>
                  );
                },
              )}
            </PassportSelectionGroup>
          );
        })}
      <EquipmentFields
        mode="old"
        managedRoles={managedRoles}
        levels={levels}
        currentData={data}
        updateField={update}
        isEditing={editing}
        passportQuery={{}}
      />
      <EquipmentMalfunctionSelector
        errorMalfunction={showError && validation?.isMalfunctionMissing}
        activeId={leaf}
        currentData={data}
        updateField={update}
        references={r}
      />
    </div>
  );
}

/** Показывает установленную замену на выбранном поездном уровне */
export function TrainReplacementEditor({ form, equipment }) {
  const { data, update } = form;
  const { replacementKey, replacementQuery, source, prettyEquipment, train } =
    equipment;
  return (
    replacementKey && (
      <div className="space-y-3">
        <EquipmentLevelSelector
          index={data.repair_type_id}
          label={
            source?.level === 2
              ? "Оборудование"
              : source?.level === 3
                ? "Компонент"
                : "Элемент"
          }
          value={data.train[replacementKey]}
          options={prettyEquipment.filter(
            (e) =>
              source &&
              e.level === source.level &&
              e.parent_id === source.parent_id,
          )}
          onChange={(value) => train(replacementKey, value)}
        />
        {data.train.passport_node_ids.length ? (
          <PassportReplacementRows
            data={{ ...data, direction: "train" }}
            updateField={update}
            query={replacementQuery}
          />
        ) : (
          <EquipmentFields
            mode="new"
            levels={{
              lvl4: source?.level === 4 ? data.train.element_id : null,
            }}
            currentData={data}
            updateField={update}
            isEditing
            passportQuery={{}}
          />
        )}
      </div>
    )
  );
}
