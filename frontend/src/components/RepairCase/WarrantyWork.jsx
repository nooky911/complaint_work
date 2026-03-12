import React from "react";
import { Archive, Bell, MessageSquare, FileText } from "lucide-react";
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
      <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase">
        {label}
      </label>
      {isEditing ? (
        <div className="flex items-center gap-1">
          <div className="w-20 shrink-0">
            <EditableField
              value={num}
              isEditing={true}
              onChange={(val) => onFieldChange(numKey, val)}
              placeholder="№"
            />
          </div>
          <div className="flex-1">
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
              ? "border-gray-200 bg-gray-50 text-gray-400"
              : "border-gray-300 bg-gray-50 text-gray-900 shadow-sm"
          }`}
        >
          <span className="truncate">
            {isMissing ? "—" : `№ ${num} от ${formatDate(date)}`}
          </span>
        </div>
      )}
    </div>
  );

  const RightPart = (
    <div className="flex w-full min-w-0 flex-col">
      <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase">
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
                  ? "border-gray-200 bg-gray-50 font-medium text-gray-400"
                  : "border-gray-300 bg-gray-50 font-medium text-gray-900 shadow-sm"
            }`}
          >
            <span className="block w-full truncate">{displaySummary}</span>
          </div>
        )}
      </Tooltip>

      {/* Файлы */}
      {caseId && relatedField && (
        <CompactWarrantyFiles
          caseId={caseId}
          isEditing={isEditing}
          relatedField={relatedField}
          onFilesUploaded={onFilesUploaded}
        />
      )}
    </div>
  );

  if (onlyLeft) return LeftPart;
  if (onlyRight) return RightPart;

  return (
    <div className="space-y-1">
      <div className="grid min-w-0 grid-cols-1 items-end gap-4 md:grid-cols-[215px_1fr]">
        {LeftPart}
        <div className="flex w-full min-w-0 flex-col">
          <label className="mb-1 ml-1 block text-xs font-bold tracking-wider text-gray-500 uppercase">
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
                      ? "border-gray-200 bg-gray-50 font-medium text-gray-400"
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
        <CompactWarrantyFiles
          caseId={caseId}
          isEditing={isEditing}
          relatedField={relatedField}
          onFilesUploaded={onFilesUploaded}
        />
      )}
    </div>
  );
}

// Компонент для обертки блока с заголовком
function WarrantyBlock({
  blockTitle,
  blockIcon,
  blockColor = "blue",
  children,
}) {
  const colorClasses = {
    blue: {
      border: "border-blue-100",
      bgFrom: "from-blue-50",
      bgTo: "to-white",
      accent: "bg-[#6766cc]",
      icon: "text-[#6766ca]",
      title: "text-[#6169ac]",
    },
    green: {
      border: "border-green-100",
      bgFrom: "from-green-50",
      bgTo: "to-white",
      accent: "bg-[#22c55e]",
      icon: "text-[#16a34a]",
      title: "text-[#15803d]",
    },
    orange: {
      border: "border-orange-100",
      bgFrom: "from-orange-50",
      bgTo: "to-white",
      accent: "bg-[#f97316]",
      icon: "text-[#ea580c]",
      title: "text-[#c2410c]",
    },
    purple: {
      border: "border-purple-100",
      bgFrom: "from-purple-50",
      bgTo: "to-white",
      accent: "bg-[#a855f7]",
      icon: "text-[#9333ea]",
      title: "text-[#7c3aed]",
    },
  };

  const colors = colorClasses[blockColor] || colorClasses.blue;

  return (
    <div className="space-y-3">
      {/* Заголовок блока */}
      <div
        className={`relative mb-3 flex items-center gap-2 rounded-lg border ${colors.border} bg-gradient-to-r ${colors.bgFrom} ${colors.bgTo} px-3 py-2 shadow-md`}
      >
        <div
          className={`absolute top-0 bottom-0 left-0 w-1 rounded-l-lg ${colors.accent}`}
        ></div>
        {blockIcon}
        <h3
          className={`text-xs font-bold tracking-wider ${colors.title} uppercase`}
        >
          {blockTitle}
        </h3>
      </div>

      {/* Контент блока */}
      <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-200/50 p-3 shadow-sm">
        {children}
      </div>
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

  return (
    <div className="space-y-3">
      {/* Блок: Уведомление */}
      <WarrantyBlock
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
      </WarrantyBlock>

      {/* Блок: Повторное уведомление */}
      <WarrantyBlock
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
      </WarrantyBlock>

      {/* Блок: Ответ поставщика */}
      <WarrantyBlock
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
      </WarrantyBlock>

      {/* Блок: Рекламационный акт / АВР */}
      <WarrantyBlock
        blockTitle={BLOCK_TITLES.warranty_claim_act_avr}
        blockIcon={<FileText className="h-4 w-4 text-[#9333ea]" />}
        blockColor="purple"
      >
        <div className="space-y-1">
          <div className="grid min-w-0 grid-cols-1 gap-4 md:grid-cols-[215px_1fr]">
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
            <CompactWarrantyFiles
              caseId={caseId}
              isEditing={isEditing}
              relatedField={WarrantyDocumentField.claim_act}
              onFilesUploaded={onFilesUploaded}
            />
          )}
        </div>
      </WarrantyBlock>

      {/* Общая кнопка скачивания всех файлов Warranty */}
      {!isEditing &&
        caseId &&
        allWarrantyFiles &&
        allWarrantyFiles.length > 1 && (
          <div className="mt-3 flex justify-end">
            <button
              onClick={() => {
                // Используем fileApi для скачивания архива всех warranty файлов
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
