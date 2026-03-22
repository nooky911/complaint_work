import React from "react";
import {
  CheckCircle,
  UserCheck,
  Mail,
  Send,
  AlertCircle,
  Clock,
  HelpCircle,
  FileText,
} from "lucide-react";

export const FileAlert = ({ className }) => (
  <div className="relative inline-flex items-center justify-center">
    <FileText className={className} />
    <AlertCircle className="absolute -top-1.5 -right-1.5 h-3.5 w-3.5 fill-red-600 stroke-[3] text-white" />
  </div>
);

const getDaysDiff = (dateStr) => {
  if (!dateStr) return 0;
  const diffTime = new Date() - new Date(dateStr);
  return Math.floor(diffTime / (1000 * 60 * 60 * 24));
};

export const getStatusConfig = (item) => {
  const rawStatus = item.status || item.calculated_status || "Новый";
  const ww = item.warranty_work || {};
  const wd = item.waybill_doc || {};

  const baseRing = "ring-2 ring-inset ring-white/50 border-transparent";

  const STYLE_RED = `bg-red-600 text-white shadow-lg ring-2 ring-inset ring-white/80`;
  const STYLE_YELLOW = `bg-yellow-400 text-slate-900 shadow-md ring-2 ring-inset ring-black/10`;
  const STYLE_GREEN = `bg-emerald-600 text-white shadow-md ${baseRing}`;
  const STYLE_ORANGE = `bg-orange-500 text-white shadow-md ${baseRing}`;

  // ЗАВЕРШЕНО
  if (rawStatus === "Завершено") {
    return { style: STYLE_GREEN, icon: CheckCircle };
  }

  // ПРОЦЕССЕ
  const orangeStatuses = [
    "Решение принято",
    "Ответ получен",
    "Уведомление отправлено",
  ];
  if (orangeStatuses.includes(rawStatus)) {
    const icons = {
      "Решение принято": UserCheck,
      "Ответ получен": Mail,
      "Уведомление отправлено": Send,
    };
    return { style: STYLE_ORANGE, icon: icons[rawStatus] || Send };
  }

  // Ожидает поступления на УЛ (15 дней от даты уведомления)
  if (rawStatus === "Ожидает поступления на УЛ") {
    const isRed = getDaysDiff(ww.notification_date) > 15;
    return {
      style: isRed ? STYLE_RED : STYLE_YELLOW,
      icon: isRed ? FileAlert : Clock,
    };
  }

  // Ожидает повторного уведомления
  if (rawStatus === "Ожидает повторного уведомления поставщика") {
    const isRed = [1, 2, 3].includes(item.repair_type_id) && !!wd.ttn_from_rc;
    return {
      style: isRed ? STYLE_RED : STYLE_YELLOW,
      icon: isRed ? FileAlert : Clock,
    };
  }

  // Ожидает отгрузки Поставщику (10 дней от даты рекл. акта)
  if (rawStatus === "Ожидает отгрузки Поставщику") {
    const isRed = getDaysDiff(ww.claim_act_date) > 10;
    return {
      style: isRed ? STYLE_RED : STYLE_YELLOW,
      icon: isRed ? FileAlert : Clock,
    };
  }

  // Ожидает восполнение (15 дней от даты ответа)
  if (rawStatus === "Ожидает восполнение от Поставщика") {
    const isRed = getDaysDiff(ww.response_letter_date) > 15;
    return {
      style: isRed ? STYLE_RED : STYLE_YELLOW,
      icon: isRed ? FileAlert : Clock,
    };
  }

  // Ожидает возврата (30 дней от ТТН к поставщику)
  if (rawStatus === "Ожидает возврата от Поставщика") {
    const isRed = getDaysDiff(wd.ttn_to_supplier_date) > 30;
    return {
      style: isRed ? STYLE_RED : STYLE_YELLOW,
      icon: isRed ? FileAlert : Clock,
    };
  }

  // Ожидает ответа / Акт исследования (30 дней от уведомления)
  if (
    rawStatus === "Ожидает ответа Поставщика" ||
    rawStatus === "Ожидает акт исследования"
  ) {
    const isRed = getDaysDiff(ww.notification_date) > 30;
    const iconDefault =
      rawStatus === "Ожидает ответа Поставщика" ? Mail : Clock;
    return {
      style: isRed ? STYLE_RED : STYLE_YELLOW,
      icon: isRed ? FileAlert : iconDefault,
    };
  }

  // Остальные "Ожидает", Рекламационный акт, Новый
  if (rawStatus.startsWith("Ожидает") || rawStatus === "Новый") {
    const baseDate = ww.notification_date || item.fault_date;
    const daysDiff = getDaysDiff(baseDate);

    // Если даты акта еще нет — статус просто желтый, не краснеет
    if (!baseDate) {
      return { style: STYLE_YELLOW, icon: AlertCircle };
    }

    // Если акт есть и прошло >= 4 дней
    if (daysDiff >= 4) {
      return { style: STYLE_RED, icon: FileAlert };
    }

    // Обычное ожидание
    return {
      style: STYLE_YELLOW,
      icon:
        rawStatus === "Ожидает уведомление поставщика" || rawStatus === "Новый"
          ? AlertCircle
          : Clock,
    };
  }

  // Дефолт (если пришло что-то совсем непонятное)
  return {
    style: `bg-slate-500 text-white shadow-md ${baseRing}`,
    icon: HelpCircle,
  };
};
