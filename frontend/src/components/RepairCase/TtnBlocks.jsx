import React from "react";
import { Truck, ArrowRight, ArrowLeft, RefreshCw } from "lucide-react";
import { BLOCK_TITLES, REPAIR_FIELDS_LABELS } from "../../constants/labels";
import { ColorBlock } from "../shared/ColorBlock";
import { formatDate } from "../../utils/formatters";
import { WaybillDocumentField } from "../../types/waybill";
import { CompactWaybillFiles } from "./CompactWaybillFiles";
import {
  EditableField,
  DatePickerField,
  SelectField,
} from "../inputs/index.jsx";

export function TtnBlocks({
  isEditing,
  ttnData,
  updateField,
  references,
  caseId,
  onFilesUploaded,
}) {
  return (
    <div className="space-y-3">
      <ColorBlock
        blockTitle={BLOCK_TITLES.ttn_replacement}
        blockIcon={<RefreshCw className="h-4 w-4" />}
        blockColor="blue"
      >
        <div className="grid grid-cols-2 gap-4">
          {isEditing ? (
            <>
              <EditableField
                label={REPAIR_FIELDS_LABELS.ttn_replacement_number}
                value={ttnData?.waybill_doc?.ttn_replacement}
                isEditing={true}
                onChange={(value) => updateField("ttn_replacement", value)}
              />
              <DatePickerField
                label={REPAIR_FIELDS_LABELS.ttn_replacement_date}
                value={ttnData?.waybill_doc?.ttn_replacement_date}
                isEditing={true}
                allowFuture={true}
                onChange={(value) => updateField("ttn_replacement_date", value)}
              />
            </>
          ) : (
            <>
              <div>
                <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                  {REPAIR_FIELDS_LABELS.ttn_replacement_number}
                </label>
                <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm font-medium text-gray-900 shadow-sm">
                  {ttnData?.waybill_doc?.ttn_replacement || "—"}
                </div>
              </div>
              <div>
                <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                  {REPAIR_FIELDS_LABELS.ttn_replacement_date}
                </label>
                <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm font-medium text-gray-900 shadow-sm">
                  {formatDate(ttnData?.waybill_doc?.ttn_replacement_date) ||
                    "—"}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Файлы ТТН замены */}
        {caseId && (
          <div className="-mt-1">
            <CompactWaybillFiles
              caseId={caseId}
              isEditing={isEditing}
              relatedField={WaybillDocumentField.ttn_replacement}
              onFilesUploaded={onFilesUploaded}
            />
          </div>
        )}
      </ColorBlock>

      <ColorBlock
        blockTitle={BLOCK_TITLES.ttn_from_rc}
        blockIcon={<Truck className="h-4 w-4" />}
        blockColor="green"
      >
        <div className="grid grid-cols-2 gap-4">
          {isEditing ? (
            <>
              <EditableField
                label={REPAIR_FIELDS_LABELS.ttn_from_rc_number}
                value={ttnData?.waybill_doc?.ttn_from_rc}
                isEditing={true}
                onChange={(value) => updateField("ttn_from_rc", value)}
              />
              <DatePickerField
                label={REPAIR_FIELDS_LABELS.ttn_from_rc_date}
                value={ttnData?.waybill_doc?.ttn_from_rc_date}
                isEditing={true}
                allowFuture={true}
                onChange={(value) => updateField("ttn_from_rc_date", value)}
              />
            </>
          ) : (
            <>
              <div>
                <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                  {REPAIR_FIELDS_LABELS.ttn_from_rc_number}
                </label>
                <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm font-medium text-gray-900 shadow-sm">
                  {ttnData?.waybill_doc?.ttn_from_rc || "—"}
                </div>
              </div>
              <div>
                <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                  {REPAIR_FIELDS_LABELS.ttn_from_rc_date}
                </label>
                <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm font-medium text-gray-900 shadow-sm">
                  {formatDate(ttnData?.waybill_doc?.ttn_from_rc_date) || "—"}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Файлы ТТН с РЦ */}
        {caseId && (
          <div className="-mt-1">
            <CompactWaybillFiles
              caseId={caseId}
              isEditing={isEditing}
              relatedField={WaybillDocumentField.ttn_from_rc}
              onFilesUploaded={onFilesUploaded}
            />
          </div>
        )}
      </ColorBlock>

      <ColorBlock
        blockTitle={BLOCK_TITLES.ttn_to_supplier}
        blockIcon={<ArrowRight className="h-4 w-4" />}
        blockColor="orange"
      >
        <div className="grid grid-cols-3 gap-4">
          {isEditing ? (
            <>
              <EditableField
                label={REPAIR_FIELDS_LABELS.ttn_to_supplier_number}
                value={ttnData?.waybill_doc?.ttn_to_supplier}
                isEditing={true}
                onChange={(value) => updateField("ttn_to_supplier", value)}
              />
              <DatePickerField
                label="Дата отгрузки"
                value={ttnData?.waybill_doc?.ttn_to_supplier_date}
                isEditing={true}
                allowFuture={true}
                onChange={(value) => updateField("ttn_to_supplier_date", value)}
              />
              <SelectField
                label={REPAIR_FIELDS_LABELS.ttn_to_supplier_provider}
                value={ttnData?.waybill_doc?.to_supplier_provider_id}
                options={references?.shipping_providers}
                isEditing={true}
                onChange={(value) =>
                  updateField("to_supplier_provider_id", value)
                }
              />
            </>
          ) : (
            <>
              <div>
                <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                  {REPAIR_FIELDS_LABELS.ttn_to_supplier_number}
                </label>
                <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm font-medium text-gray-900 shadow-sm">
                  {ttnData?.waybill_doc?.ttn_to_supplier || "—"}
                </div>
              </div>
              <div>
                <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                  Дата отгрузки
                </label>
                <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm font-medium text-gray-900 shadow-sm">
                  {formatDate(ttnData?.waybill_doc?.ttn_to_supplier_date) ||
                    "—"}
                </div>
              </div>
              <div>
                <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                  {REPAIR_FIELDS_LABELS.ttn_to_supplier_provider}
                </label>
                <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm font-medium text-gray-900 shadow-sm">
                  {ttnData?.waybill_doc?.to_supplier_provider?.name ||
                    (ttnData?.waybill_doc?.to_supplier_provider_id &&
                      references?.shipping_providers?.find(
                        (p) =>
                          p.id === ttnData.waybill_doc.to_supplier_provider_id,
                      )?.name) ||
                    "—"}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Файлы ТТН поставщику */}
        {caseId && (
          <div className="-mt-1">
            <CompactWaybillFiles
              caseId={caseId}
              isEditing={isEditing}
              relatedField={WaybillDocumentField.ttn_to_supplier}
              onFilesUploaded={onFilesUploaded}
            />
          </div>
        )}
      </ColorBlock>

      <ColorBlock
        blockTitle={BLOCK_TITLES.ttn_from_supplier}
        blockIcon={<ArrowLeft className="h-4 w-4" />}
        blockColor="purple"
      >
        <div className="grid grid-cols-3 gap-4">
          {isEditing ? (
            <>
              <EditableField
                label={REPAIR_FIELDS_LABELS.ttn_from_supplier_number}
                value={ttnData?.waybill_doc?.ttn_from_supplier}
                isEditing={true}
                onChange={(value) => updateField("ttn_from_supplier", value)}
              />
              <DatePickerField
                label={REPAIR_FIELDS_LABELS.ttn_from_supplier_date}
                value={ttnData?.waybill_doc?.ttn_from_supplier_date}
                isEditing={true}
                allowFuture={true}
                onChange={(value) =>
                  updateField("ttn_from_supplier_date", value)
                }
              />
              <SelectField
                label={REPAIR_FIELDS_LABELS.ttn_from_supplier_provider}
                value={ttnData?.waybill_doc?.from_supplier_provider_id}
                options={references?.shipping_providers?.slice(0, 5)}
                isEditing={true}
                onChange={(value) =>
                  updateField("from_supplier_provider_id", value)
                }
              />
            </>
          ) : (
            <>
              <div>
                <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                  {REPAIR_FIELDS_LABELS.ttn_from_supplier_number}
                </label>
                <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm font-medium text-gray-900 shadow-sm">
                  {ttnData?.waybill_doc?.ttn_from_supplier || "—"}
                </div>
              </div>
              <div>
                <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                  {REPAIR_FIELDS_LABELS.ttn_from_supplier_date}
                </label>
                <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm font-medium text-gray-900 shadow-sm">
                  {formatDate(ttnData?.waybill_doc?.ttn_from_supplier_date) ||
                    "—"}
                </div>
              </div>
              <div>
                <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                  {REPAIR_FIELDS_LABELS.ttn_from_supplier_provider}
                </label>
                <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3 text-sm font-medium text-gray-900 shadow-sm">
                  {ttnData?.waybill_doc?.from_supplier_provider?.name ||
                    (ttnData?.waybill_doc?.from_supplier_provider_id &&
                      references?.shipping_providers?.slice(0, 5).find(
                        (p) =>
                          p.id ===
                          ttnData.waybill_doc.from_supplier_provider_id,
                      )?.name) ||
                    "—"}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Файлы ТТН от поставщика */}
        {caseId && (
          <div className="-mt-1">
            <CompactWaybillFiles
              caseId={caseId}
              isEditing={isEditing}
              relatedField={WaybillDocumentField.ttn_from_supplier}
              onFilesUploaded={onFilesUploaded}
            />
          </div>
        )}
      </ColorBlock>
    </div>
  );
}
