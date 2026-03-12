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

export const getStatusConfig = (item) => {
  const rawStatus = item.status || "Новый";

  const baseRing = "ring-2 ring-inset ring-white/50 border-transparent";

  // ЗАВЕРШЕНО
  if (rawStatus === "Завершено") {
    return {
      style: `bg-emerald-600 text-white shadow-md ${baseRing}`,
      icon: CheckCircle,
    };
  }

  // В ПРОЦЕССЕ
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
    return {
      style: `bg-orange-500 text-white shadow-md ${baseRing}`,
      icon: icons[rawStatus] || Send,
    };
  }

  // ОЖИДАНИЕ / ПРОСРОЧКА / НОВЫЙ
  if (rawStatus.startsWith("Ожидает") || rawStatus === "Новый") {
    const baseDate =
      item.warranty_work?.notification_date ||
      item.date_recorded ||
      item.created_at;

    const daysDiff = baseDate
      ? Math.floor((new Date() - new Date(baseDate)) / (1000 * 60 * 60 * 24))
      : 0;

    // Если просрочка больше 4 дней
    if (daysDiff >= 4) {
      return {
        style: `bg-red-600 text-white shadow-lg ring-2 ring-inset ring-white/80`,
        icon: FileAlert,
      };
    }

    // Обычное ожидание
    return {
      style: `bg-yellow-400 text-slate-900 shadow-md ring-2 ring-inset ring-black/10`,
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
