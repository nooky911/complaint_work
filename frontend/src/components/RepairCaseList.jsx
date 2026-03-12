import React from "react";
import {
  AlertCircle,
  Train,
  Calendar,
  MapPin,
  Package,
  Wrench,
  Building2,
  Mail,
  FileCheck,
  ClipboardCheck,
  User,
  Repeat,
} from "lucide-react";

import { formatDate, getText, formatFullName } from "../utils/formatters";
import { getStatusConfig } from "../utils/statusHelpers";
import { REPAIR_FIELDS_LABELS } from "../constants/labels";

const NumberIcon = () => (
  <span className="text-xl leading-none font-black text-amber-300 select-none">
    №
  </span>
);

// Вспомогательные компоненты
const DataHeader = ({ label, value, icon: Icon, iconColor }) => (
  <div className="flex items-center gap-2">
    <Icon className={`h-6 w-6 ${iconColor}`} />
    <div>
      <p className="text-[10px] font-bold text-purple-200 uppercase">{label}</p>
      <p className="text-xl font-black text-white drop-shadow-[0_2px_2px_rgba(0,0,0,0.5)]">
        {value}
      </p>
    </div>
  </div>
);
const EquipmentBlock = ({ label, value, serial, icon: Icon, color }) => (
  <div>
    <div className={`mb-1 flex items-center gap-2 font-black ${color}`}>
      <Icon className="h-5 w-5" />
      <span className="text-xs tracking-wider uppercase">{label}</span>
    </div>
    <p className="text-sm font-black text-slate-900">{value}</p>
    {serial && (
      <p className="mt-1 text-[12px] font-medium text-slate-900">
        зав. №{" "}
        <span className="text-[13px] font-black text-slate-900">{serial}</span>
      </p>
    )}
  </div>
);

const DocItem = ({ icon: Icon, label, num, date, summary, color }) => {
  const colorMap = {
    blue: "text-blue-700 border-blue-600",
    indigo: "text-indigo-700 border-indigo-600",
    purple: "text-purple-700 border-purple-600",
    amber: "text-amber-700 border-orange-600",
    emerald: "text-emerald-700 border-emerald-600",
  };

  return (
    <div className="text-sm">
      <Icon
        className={`mr-2 inline h-4 w-4 align-text-bottom ${color && colorMap[color] ? colorMap[color].split(" ")[0] : "text-slate-700"}`}
      />
      <span
        className={`mr-2 text-[10px] font-black uppercase ${color && colorMap[color] ? colorMap[color].split(" ")[0].replace("600", "700") : "text-slate-900"}`}
      >
        {label}
      </span>
      {num || date ? (
        <div className="flex items-center whitespace-nowrap">
          {num && (
            <span className="mr-1 font-bold text-slate-900">№ {num}</span>
          )}
          {date && (
            <span className="text-slate-900">
              от <span className="font-bold">{formatDate(date)}</span>
            </span>
          )}
        </div>
      ) : (
        <span className="font-bold text-slate-900">—</span>
      )}
      {summary && (
        <p
          className={`mt-1 border-l-2 pl-2 text-[13px] font-bold text-slate-900 ${color && colorMap[color] ? colorMap[color].split(" ")[1] : "border-slate-600"}`}
        >
          {typeof summary === "object"
            ? summary.name || summary.summary
            : summary}
        </p>
      )}
    </div>
  );
};

export function RepairCaseList({ cases, onCaseClick }) {
  if (!cases || cases.length === 0) {
    return (
      <div className="flex h-28 items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 text-slate-500">
        Записи не найдены
      </div>
    );
  }

  return (
    <div className="h-full min-h-0 space-y-3 overflow-y-auto p-2">
      {cases.map((item, index) => {
        const status = getStatusConfig(item);
        const StatusIcon = status.icon;

        return (
          <div
            key={item.id}
            onClick={() => onCaseClick(item, index)}
            className="group relative min-h-[280px] flex-shrink-0 cursor-pointer overflow-hidden rounded-2xl border border-slate-300 bg-white shadow-sm transition-all duration-200 hover:border-purple-400 hover:shadow-lg active:scale-[0.99]"
          >
            {/* БЛОК 1: ШАПКА */}
            <div className="bg-[#6766cc] p-3 text-white">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-[18px] font-black drop-shadow-[0_2px_2px_rgba(0,0,0,0.4)]">
                    # {item.displayNumber}
                  </span>
                  <div
                    className={`flex items-center gap-1.5 rounded-lg px-3 py-1 text-xs font-black tracking-wide uppercase shadow-sm ${status.style}`}
                  >
                    <StatusIcon className="h-4 w-4" />
                    {item.status || "Ожидает уведомление"}
                  </div>
                </div>
                <div className="flex items-center gap-2 rounded-md border-l-[4px] border-l-indigo-400 bg-white px-3 py-1 shadow-lg ring-1 ring-black/5">
                  <User
                    className="h-3.5 w-3.5 text-indigo-600"
                    strokeWidth={3}
                  />
                  <span className="text-[11px] font-black tracking-tight text-slate-900 uppercase">
                    {formatFullName(item.creator_full_name)}
                  </span>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-6">
                <DataHeader
                  label="Тип эл-за"
                  value={getText(item.locomotive_model)}
                  icon={Train}
                  iconColor="text-cyan-300"
                />
                <DataHeader
                  label="Номер"
                  value={item.locomotive_number || "—"}
                  icon={NumberIcon}
                  iconColor="text-amber-300"
                />
                <DataHeader
                  label="РЦ"
                  value={getText(item.regional_center)}
                  icon={MapPin}
                  iconColor="text-rose-300"
                />
                <DataHeader
                  label="Дата выявления"
                  value={formatDate(item.fault_date)}
                  icon={Calendar}
                  iconColor="text-emerald-300"
                />

                <div className="ml-auto flex items-center gap-3 rounded-xl border-2 border-violet-300 bg-gradient-to-r from-violet-100 to-fuchsia-100 px-3 py-1 shadow-md">
                  <Building2 className="h-5 w-5 text-violet-600" />
                  <div>
                    <p className="text-[10px] font-bold text-violet-700 uppercase">
                      Поставщик
                    </p>
                    <p className="text-sm font-bold text-slate-900">
                      {getText(item.supplier)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-b-4 border-blue-400/40 bg-white p-4 text-slate-900">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                <EquipmentBlock
                  label="Оборудование"
                  value={`${item.component_equipment?.parent ? getText(item.component_equipment.parent) + " " : ""}${getText(item.component_equipment)}${item.component_quantity > 1 ? ` (${item.component_quantity} шт.)` : ""}`}
                  serial={item.component_serial_number_old}
                  icon={Package}
                  color="text-blue-800"
                />
                <EquipmentBlock
                  label={REPAIR_FIELDS_LABELS.element}
                  value={
                    item.element_equipment
                      ? `${getText(item.element_equipment)}${item.element_quantity > 1 ? ` (${item.element_quantity} шт.)` : ""}`
                      : "—"
                  }
                  serial={item.element_serial_number_old}
                  icon={Wrench}
                  color="text-indigo-800"
                />
                <EquipmentBlock
                  label={REPAIR_FIELDS_LABELS.malfunction}
                  value={getText(item.malfunction)}
                  icon={AlertCircle}
                  color="text-red-700"
                />
              </div>
            </div>

            <div className="bg-white p-4 text-slate-900">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
                <DocItem
                  icon={Mail}
                  label="Уведомление"
                  num={item.warranty_work?.notification_number}
                  date={item.warranty_work?.notification_date}
                  summary={item.warranty_work?.notification_summary}
                  color="blue"
                />
                <DocItem
                  icon={Repeat}
                  label="Повт. Увед."
                  num={item.warranty_work?.re_notification_number}
                  date={item.warranty_work?.re_notification_date}
                  color="indigo"
                />
                <DocItem
                  icon={Mail}
                  label="Ответ"
                  num={item.warranty_work?.response_letter_number}
                  date={item.warranty_work?.response_letter_date}
                  summary={item.warranty_work?.response_summary}
                  color="purple"
                />
                <DocItem
                  icon={FileCheck}
                  label="Рекл. Акт"
                  num={item.warranty_work?.claim_act_number}
                  date={item.warranty_work?.claim_act_date}
                  summary={
                    item.warranty_work?.claim_act_number
                      ? item.warranty_work?.decision_summary
                      : null
                  }
                  color="amber"
                />
                <DocItem
                  icon={ClipboardCheck}
                  label="АВР"
                  num={item.warranty_work?.work_completion_act_number}
                  date={item.warranty_work?.work_completion_act_date}
                  summary={
                    item.warranty_work?.work_completion_act_number
                      ? item.warranty_work?.decision_summary
                      : null
                  }
                  color="emerald"
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
