import React, { useState } from "react";

import { PassportEquipmentSelector } from "./PassportEquipmentFields";
import { EditableField } from "../inputs";
import { REPAIR_FIELDS_LABELS } from "../../constants/labels";
import {
  MANUFACTURE_DATE_ERROR,
  isValidManufactureDate,
} from "../../utils/validators";

/** Показывает паспортный выбор или ручные поля для оборудования без паспорта */
export const EquipmentFields = ({
  mode,
  levels,
  currentData,
  updateField,
  isEditing,
  passportQuery,
}) => {
  const hasPassport =
    mode === "old" &&
    !!(currentData?.passport_id && currentData?.component_equipment_id);
  const managedRoles = hasPassport
    ? passportQuery.data?.required_roles || []
    : [];
  const loadingPassport =
    hasPassport && (!passportQuery.data || passportQuery.isError);
  const sfx = mode === "old" ? "_old" : "_new";
  const [rejectedDates, setRejectedDates] = useState({});

  const handleManufactureDateChange = (field, value) => {
    const invalid = !isValidManufactureDate(value);
    setRejectedDates((previous) => ({ ...previous, [field]: invalid }));
    if (!invalid) updateField(field, value);
  };

  const manufactureDateError = (field) =>
    rejectedDates[field] || !isValidManufactureDate(currentData?.[field])
      ? MANUFACTURE_DATE_ERROR
      : undefined;

  const rId = Number(
    currentData?.repair_type?.id || currentData?.repair_type_id,
  );

  const showComponent =
    mode === "old"
      ? true
      : [1, 2].includes(rId) || (rId === 8 && !levels?.lvl4);

  const showElement =
    mode === "old"
      ? !!levels?.lvl4
      : rId === 3 || (rId === 8 && !!levels?.lvl4);

  const disableComponent = mode === "old" ? !levels?.lvl3 : false;
  const disableElement = mode === "old" ? !levels?.lvl4 : false;

  const handleQuantityChange = (field, val) => {
    if (val === "" || val === null || val === undefined) {
      updateField(field, "");
    } else {
      updateField(field, Number(val));
    }
  };

  return (
    <div className="space-y-3 pt-2">
      {hasPassport &&
        (currentData?.section_mask ? (
          <PassportEquipmentSelector
            data={currentData}
            updateField={updateField}
            query={passportQuery}
          />
        ) : (
          <p className="text-xs text-slate-500">
            Выберите секцию, чтобы увидеть оборудование из паспорта
          </p>
        ))}
      {/* Поля Component (Lvl 3) */}
      {showComponent &&
        !loadingPassport &&
        !managedRoles.includes("component") && (
          <div className="flex gap-3">
            <div className="w-24 shrink-0">
              <EditableField
                label={REPAIR_FIELDS_LABELS.quantity}
                value={
                  mode === "old"
                    ? (currentData?.component_quantity ?? "")
                    : (currentData?.new_component_quantity ?? "")
                }
                onChange={(val) =>
                  handleQuantityChange(
                    mode === "old"
                      ? "component_quantity"
                      : "new_component_quantity",
                    val,
                  )
                }
                isEditing={isEditing}
                type="number"
                isDisabled={disableComponent}
              />
            </div>
            <div className="flex-1">
              <EditableField
                label={REPAIR_FIELDS_LABELS.component_serial_number}
                value={
                  mode === "old"
                    ? currentData?.component_serial_number_old
                    : currentData?.component_serial_number_new
                }
                onChange={(val) =>
                  updateField(`component_serial_number${sfx}`, val)
                }
                isEditing={isEditing}
                isDisabled={disableComponent}
              />
            </div>
            <div className="flex-1">
              <EditableField
                label={REPAIR_FIELDS_LABELS.manufacture_date}
                value={
                  mode === "old"
                    ? currentData?.component_manufacture_date_old
                    : currentData?.component_manufacture_date_new
                }
                onChange={(val) =>
                  handleManufactureDateChange(
                    `component_manufacture_date${sfx}`,
                    val,
                  )
                }
                error={manufactureDateError(`component_manufacture_date${sfx}`)}
                isEditing={isEditing}
                type="text"
                isDisabled={disableComponent}
              />
            </div>
          </div>
        )}

      {/* Поля Element (Lvl 4) */}
      {showElement && !loadingPassport && !managedRoles.includes("element") && (
        <div className="flex gap-3">
          <div className="w-24 shrink-0">
            <EditableField
              label={REPAIR_FIELDS_LABELS.quantity}
              value={
                mode === "old"
                  ? (currentData?.element_quantity ?? "")
                  : (currentData?.new_element_quantity ?? "")
              }
              onChange={(val) =>
                handleQuantityChange(
                  mode === "old" ? "element_quantity" : "new_element_quantity",
                  val,
                )
              }
              isEditing={isEditing}
              type="number"
              isDisabled={disableElement}
            />
          </div>
          <div className="flex-1">
            <EditableField
              label={REPAIR_FIELDS_LABELS.element_serial_number}
              value={
                mode === "old"
                  ? currentData?.element_serial_number_old
                  : currentData?.element_serial_number_new
              }
              onChange={(val) =>
                updateField(`element_serial_number${sfx}`, val)
              }
              isEditing={isEditing}
              isDisabled={disableElement}
            />
          </div>
          <div className="flex-1">
            <EditableField
              label={REPAIR_FIELDS_LABELS.manufacture_date}
              value={
                mode === "old"
                  ? currentData?.element_manufacture_date_old
                  : currentData?.element_manufacture_date_new
              }
              onChange={(val) =>
                handleManufactureDateChange(
                  `element_manufacture_date${sfx}`,
                  val,
                )
              }
              error={manufactureDateError(`element_manufacture_date${sfx}`)}
              isEditing={isEditing}
              type="text"
              isDisabled={disableElement}
            />
          </div>
        </div>
      )}
    </div>
  );
};
