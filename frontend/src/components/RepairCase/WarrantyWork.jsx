import React from "react";
import { Archive, Bell, MessageSquare, FileText, Search } from "lucide-react";
import { formatDate, getText } from "../../utils/formatters";
import {
  SelectField,
  DatePickerField,
  EditableField,
} from "../inputs/index.jsx";
import { REPAIR_FIELDS_LABELS, BLOCK_TITLES } from "../../constants/labels";
import { Tooltip } from "../../utils/Tooltip";
import { CompactWarrantyFiles } from "./CompactWarrantyFiles";
import { WarrantyDocumentField } from "../../types/warranty";
import { useUnifiedFileManagement } from "../../hooks/useUnifiedFileManagement";
import { ColorBlock } from "../shared/ColorBlock";

function FileRow({
  label,
  num,
  date,
  numKey,
  dateKey,
  summary,
  summaryLabel,
  summaryLabelId,
  summaryOptions,
  isEditing,
  isMissing,
  onFieldChange,
  onlyLeft = false,
  onlyRight = false,
  isAutoSummary = false,
  caseId,
  relatedField,
  onFilesUploaded,
}) {
  const getAutoSummaryText = () => {
    if (num && date && !date.includes("_")) {
      return "Командировать представителя";
    }
    return "—";
  };

  const displaySummary = isAutoSummary ? getAutoSummaryText() : summary;
  const summaryTooltipText = isEditing
    ? summaryOptions?.find((opt) => opt.id === summary)?.name || displaySummary
    : displaySummary;

  const LeftPart = (
    <div className="flex min-w-0 flex-col">
      <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-slate-500 uppercase antialiased">
        {label}
      </label>
      {isEditing ? (
        <div className="flex items-center gap-1">
          <div className="flex-1">
            <EditableField
              value={num}
              isEditing={true}
              onChange={(val) => onFieldChange(numKey, val)}
              placeholder="№"
            />
          </div>
          <div className="w-36 shrink-0">
            <DatePickerField
              value={date}
              isEditing={true}
              onChange={(val) => onFieldChange(dateKey, val)}
            />
          </div>
        </div>
      ) : (
        <div
          className={`flex h-[38px] items-center rounded-lg border px-3 text-sm font-medium transition-all ${
            isMissing
              ? "border border-gray-300 bg-gray-50 text-gray-900 shadow-sm"
              : "border-gray-300 bg-gray-50 text-gray-900 shadow-sm"
          }`}
        >
          <span className="whitespace-nowrap">
            {isMissing ? "—" : `${num} от ${formatDate(date)}`}
          </span>
        </div>
      )}
    </div>
  );

  const RightPart = (
    <div className="flex w-full min-w-0 flex-col">
      <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
        {summaryLabel || "Содержание"}
      </label>
      <Tooltip
        text={
          summaryTooltipText && summaryTooltipText !== "—"
            ? summaryTooltipText
            : null
        }
      >
        {isEditing && !isAutoSummary && summaryLabelId ? (
          <div className="w-full">
            <SelectField
              label={null}
              value={summary}
              options={summaryOptions}
              isEditing={true}
              onChange={(value) => onFieldChange(summaryLabelId, value)}
              placeholder="—"
            />
          </div>
        ) : (
          <div
            className={`flex h-[38px] items-center overflow-hidden rounded-lg border px-3 text-sm transition-all ${
              isEditing && isAutoSummary
                ? "border-gray-200 bg-white font-bold text-slate-900 shadow-sm"
                : displaySummary === "—"
                  ? "border border-gray-300 bg-gray-50 font-medium text-gray-900 shadow-sm"
                  : "border-gray-300 bg-gray-50 font-medium text-gray-900 shadow-sm"
            }`}
          >
            <span className="block w-full truncate">{displaySummary}</span>
          </div>
        )}
      </Tooltip>

      {/* Файлы */}
      {caseId && relatedField && (
        <div className="mt-2">
          <CompactWarrantyFiles
            caseId={caseId}
            isEditing={isEditing}
            relatedField={relatedField}
            onFilesUploaded={onFilesUploaded}
          />
        </div>
      )}
    </div>
  );

  if (onlyLeft) return LeftPart;
  if (onlyRight) return RightPart;

  return (
    <div className="space-y-1">
      <div className="grid min-w-0 grid-cols-1 items-end gap-4 md:grid-cols-[minmax(215px,_max-content)_1fr]">
        {LeftPart}
        <div className="flex w-full min-w-0 flex-col">
          <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
            {summaryLabel || "Содержание"}
          </label>
          <Tooltip
            text={
              summaryTooltipText && summaryTooltipText !== "—"
                ? summaryTooltipText
                : null
            }
          >
            {isEditing && !isAutoSummary && summaryLabelId ? (
              <div className="w-full">
                <SelectField
                  label={null}
                  value={summary}
                  options={summaryOptions}
                  isEditing={true}
                  onChange={(value) => onFieldChange(summaryLabelId, value)}
                  placeholder="—"
                />
              </div>
            ) : (
              <div
                className={`flex h-[38px] items-center overflow-hidden rounded-lg border px-3 text-sm transition-all ${
                  isEditing && isAutoSummary
                    ? "border-gray-200 bg-white font-bold text-slate-900 shadow-sm"
                    : displaySummary === "—"
                      ? "border border-gray-300 bg-gray-50 font-medium text-gray-900 shadow-sm"
                      : "border-gray-300 bg-gray-50 font-medium text-gray-900 shadow-sm"
                }`}
              >
                <span className="block w-full truncate">{displaySummary}</span>
              </div>
            )}
          </Tooltip>
        </div>
      </div>

      {/* Бар файлов под строкой */}
      {caseId && relatedField && (
        <div className="mt-2">
          <CompactWarrantyFiles
            caseId={caseId}
            isEditing={isEditing}
            relatedField={relatedField}
            onFilesUploaded={onFilesUploaded}
          />
        </div>
      )}
    </div>
  );
}

export const WarrantyWork = ({
  isEditing,
  currentData,
  repairCase,
  updateWarrantyField,
  references,
  caseId,
  onFilesUploaded,
}) => {
  const data = isEditing
    ? currentData?.warranty_work
    : repairCase?.warranty_work;

  // Получаем все warranty-файлы для проверки количества
  const { files: allWarrantyFiles } = useUnifiedFileManagement(caseId, {
    category: "warranty",
    useReactQuery: true,
  });

  const decisionFullText = isEditing
    ? references?.decision_summaries?.find(
        (opt) => opt.id === data?.decision_summary_id,
      )?.name
    : getText(data?.decision_summary);

  const isReasonDisabled =
    isEditing &&
    (!data?.research_status_id || [3, 5, 6].includes(data?.research_status_id));

  const getFilteredReasonOptions = () => {
    if (!references?.investigation_reasons) return [];

    const researchStatusId = data?.research_status_id;

    if (researchStatusId === 1) {
      return references.investigation_reasons.filter(
        (reason) => reason.id >= 1 && reason.id <= 5,
      );
    } else if (researchStatusId === 2 || researchStatusId === 4) {
      return references.investigation_reasons.filter(
        (reason) => reason.id >= 6 && reason.id <= 9,
      );
    }

    return references.investigation_reasons;
  };

  const handleStatusChange = (value) => {
    updateWarrantyField("research_status_id", value);

    if (!value || [3, 5, 6].includes(value)) {
      updateWarrantyField("investigation_reason_id", null);
    } else {
      const currentReasonId = data?.investigation_reason_id;
      let filteredOptions = [];

      if (value === 1) {
        filteredOptions =
          references?.investigation_reasons?.filter(
            (reason) => reason.id >= 1 && reason.id <= 5,
          ) || [];
      } else if (value === 2 || value === 4) {
        filteredOptions =
          references?.investigation_reasons?.filter(
            (reason) => reason.id >= 6 && reason.id <= 9,
          ) || [];
      }

      if (
        currentReasonId &&
        !filteredOptions.find((opt) => opt.id === currentReasonId)
      ) {
        updateWarrantyField("investigation_reason_id", null);
      }
    }
  };

  return (
    <div className="space-y-3">
      {/* Блок: Уведомление */}
      <ColorBlock
        blockTitle={BLOCK_TITLES.warranty_notification}
        blockIcon={<Bell className="h-4 w-4 text-[#6766ca]" />}
        blockColor="blue"
      >
        <FileRow
          label="№ и дата ув-ия"
          num={data?.notification_number}
          date={data?.notification_date}
          numKey="notification_number"
          dateKey="notification_date"
          summary={
            isEditing
              ? data?.notification_summary_id
              : getText(data?.notification_summary)
          }
          summaryLabel={REPAIR_FIELDS_LABELS.summary}
          summaryLabelId="notification_summary_id"
          summaryOptions={references?.notification_summaries}
          isEditing={isEditing}
          isMissing={!data?.notification_number}
          onFieldChange={updateWarrantyField}
          caseId={caseId}
          relatedField={WarrantyDocumentField.notification}
          onFilesUploaded={onFilesUploaded}
        />
      </ColorBlock>

      {/* Блок: Повторное уведомление */}
      <ColorBlock
        blockTitle={BLOCK_TITLES.warranty_re_notification}
        blockIcon={<Bell className="h-4 w-4 text-[#16a34a]" />}
        blockColor="green"
      >
        <FileRow
          label="№ и дата повт. ув-ия"
          num={data?.re_notification_number}
          date={data?.re_notification_date}
          numKey="re_notification_number"
          dateKey="re_notification_date"
          summary={getText(data?.re_notification_summary)}
          summaryLabel={REPAIR_FIELDS_LABELS.summary}
          isEditing={isEditing}
          isMissing={!data?.re_notification_number}
          onFieldChange={updateWarrantyField}
          isAutoSummary={true}
          caseId={caseId}
          relatedField={WarrantyDocumentField.re_notification}
          onFilesUploaded={onFilesUploaded}
        />
      </ColorBlock>

      {/* Блок: Ответ поставщика */}
      <ColorBlock
        blockTitle={BLOCK_TITLES.warranty_supplier_response}
        blockIcon={<MessageSquare className="h-4 w-4 text-[#ea580c]" />}
        blockColor="orange"
      >
        <FileRow
          label="№ и дата ответа"
          num={data?.response_letter_number}
          date={data?.response_letter_date}
          numKey="response_letter_number"
          dateKey="response_letter_date"
          summary={
            isEditing
              ? data?.response_summary_id
              : getText(data?.response_summary)
          }
          summaryLabel={REPAIR_FIELDS_LABELS.summary}
          summaryLabelId="response_summary_id"
          summaryOptions={references?.response_summaries}
          isEditing={isEditing}
          isMissing={!data?.response_letter_number}
          onFieldChange={updateWarrantyField}
          caseId={caseId}
          relatedField={WarrantyDocumentField.response}
          onFilesUploaded={onFilesUploaded}
        />
      </ColorBlock>

      {/* Блок: Рекламационный акт / АВР */}
      <ColorBlock
        blockTitle={BLOCK_TITLES.warranty_claim_act_avr}
        blockIcon={<FileText className="h-4 w-4 text-[#9333ea]" />}
        blockColor="purple"
      >
        <div className="space-y-1">
          <div className="grid min-w-0 grid-cols-1 gap-4 md:grid-cols-[minmax(215px,_max-content)_1fr]">
            <div className="flex min-w-0 flex-col gap-3">
              <FileRow
                label="№ и дата РА"
                num={data?.claim_act_number}
                date={data?.claim_act_date}
                numKey="claim_act_number"
                dateKey="claim_act_date"
                isEditing={isEditing}
                onFieldChange={updateWarrantyField}
                onlyLeft={true}
                isMissing={!data?.claim_act_number}
              />
              <FileRow
                label="№ и дата АВР"
                num={data?.work_completion_act_number}
                date={data?.work_completion_act_date}
                numKey="work_completion_act_number"
                dateKey="work_completion_act_date"
                isEditing={isEditing}
                onFieldChange={updateWarrantyField}
                onlyLeft={true}
                isMissing={!data?.work_completion_act_number}
              />
            </div>
            <div className="flex w-full min-w-0 flex-col justify-center">
              <FileRow
                label="Краткое содержание"
                summary={
                  isEditing ? data?.decision_summary_id : decisionFullText
                }
                summaryLabel={REPAIR_FIELDS_LABELS.summary}
                summaryLabelId="decision_summary_id"
                summaryOptions={references?.decision_summaries}
                isEditing={isEditing}
                onFieldChange={updateWarrantyField}
                onlyRight={true}
                caseId={caseId}
                relatedField={WarrantyDocumentField.decision}
                onFilesUploaded={onFilesUploaded}
              />
            </div>
          </div>

          {/* Файлы РА */}
          {caseId && (
            <div className="mt-2">
              <CompactWarrantyFiles
                caseId={caseId}
                isEditing={isEditing}
                relatedField={WarrantyDocumentField.claim_act}
                onFilesUploaded={onFilesUploaded}
              />
            </div>
          )}
        </div>
      </ColorBlock>

      {/* Блок: Акт исследования */}
      <ColorBlock
        blockTitle={BLOCK_TITLES.warranty_research_act}
        blockIcon={<Search className="h-4 w-4 text-[#ca8a04]" />}
        blockColor="yellow"
      >
        <div className="space-y-3">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="flex min-w-0 flex-col">
              <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
                Статус по результатам исследования
              </label>
              {isEditing ? (
                <SelectField
                  label={null}
                  value={data?.research_status_id}
                  options={references?.research_statuses}
                  isEditing={true}
                  onChange={handleStatusChange}
                  placeholder="—"
                />
              ) : (
                <div
                  className={`flex h-[38px] items-center rounded-lg border px-3 text-sm font-medium transition-all ${
                    data?.research_status_id
                      ? "border border-gray-300 bg-gray-50 text-gray-900 shadow-sm"
                      : "border border-gray-300 bg-gray-50 text-gray-900 shadow-sm"
                  }`}
                >
                  <span className="truncate">
                    {getText(data?.research_status) || "—"}
                  </span>
                </div>
              )}
            </div>

            <div className="flex min-w-0 flex-col">
              <label
                className={`mb-1 ml-1 block text-xs font-bold tracking-wider uppercase antialiased ${
                  isReasonDisabled ? "text-gray-400" : "text-gray-500"
                }`}
              >
                Причина
              </label>
              {isEditing ? (
                <div
                  className={`w-full ${
                    isReasonDisabled ? "cursor-not-allowed opacity-50" : ""
                  }`}
                >
                  <SelectField
                    label={null}
                    value={data?.investigation_reason_id}
                    options={getFilteredReasonOptions()}
                    isEditing={true}
                    onChange={(value) =>
                      updateWarrantyField("investigation_reason_id", value)
                    }
                    placeholder="—"
                    disabled={isReasonDisabled}
                  />
                </div>
              ) : (
                <div
                  className={`flex h-[38px] items-center rounded-lg border px-3 text-sm font-medium transition-all ${
                    data?.investigation_reason_id
                      ? "border border-gray-300 bg-gray-50 text-gray-900 shadow-sm"
                      : "border border-gray-300 bg-gray-50 text-gray-900 shadow-sm"
                  }`}
                >
                  <span className="truncate">
                    {getText(data?.investigation_reason) || "—"}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex min-w-0 flex-col">
            <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase antialiased">
              № и дата документа об исследовании
            </label>
            {isEditing ? (
              <EditableField
                value={data?.research_document}
                isEditing={true}
                onChange={(value) =>
                  updateWarrantyField("research_document", value)
                }
                placeholder="№ и дата документа"
              />
            ) : (
              <div
                className={`flex h-[38px] items-center rounded-lg border px-3 text-sm font-medium transition-all ${
                  data?.research_document
                    ? "border border-gray-300 bg-gray-50 text-gray-900 shadow-sm"
                    : "border border-gray-300 bg-gray-50 text-gray-900 shadow-sm"
                }`}
              >
                <span className="truncate">
                  {data?.research_document || "—"}
                </span>
              </div>
            )}

            {/* Файлы акта исследования */}
            {caseId && (
              <div className="mt-2">
                <CompactWarrantyFiles
                  caseId={caseId}
                  isEditing={isEditing}
                  relatedField={WarrantyDocumentField.research_document}
                  onFilesUploaded={onFilesUploaded}
                />
              </div>
            )}
          </div>
        </div>
      </ColorBlock>

      {/* Общая кнопка скачивания всех файлов Warranty */}
      {!isEditing &&
        caseId &&
        allWarrantyFiles &&
        allWarrantyFiles.length > 1 && (
          <div className="mt-3 flex justify-end">
            <button
              onClick={() => {
                import("../../api/files").then(({ fileApi }) => {
                  fileApi.downloadArchive(caseId, "warranty");
                });
              }}
              className="flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-2 py-1 text-[11px] font-bold text-slate-600 shadow-sm transition-all hover:border-indigo-300 hover:text-indigo-600 active:scale-95"
            >
              <Archive className="h-3.5 w-3.5" /> СКАЧАТЬ ВСЕ ФАЙЛЫ
            </button>
          </div>
        )}
    </div>
  );
};
