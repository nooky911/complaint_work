import React, { useEffect } from "react";
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from "lucide-react";

const toastConfig = {
  error: {
    bgColor: 'bg-white',
    borderColor: 'border-red-100',
    iconBg: 'bg-red-50',
    iconColor: 'text-red-500',
    icon: AlertCircle
  },
  success: {
    bgColor: 'bg-white',
    borderColor: 'border-green-100',
    iconBg: 'bg-green-50',
    iconColor: 'text-green-500',
    icon: CheckCircle
  },
  warning: {
    bgColor: 'bg-white',
    borderColor: 'border-yellow-100',
    iconBg: 'bg-yellow-50',
    iconColor: 'text-yellow-500',
    icon: AlertTriangle
  },
  info: {
    bgColor: 'bg-white',
    borderColor: 'border-blue-100',
    iconBg: 'bg-blue-50',
    iconColor: 'text-blue-500',
    icon: Info
  }
};

export const ErrorToast = ({ show, onClose, title, message, type = 'error' }) => {
  useEffect(() => {
    if (show) {
      const timer = setTimeout(() => onClose(), 6000);
      return () => clearTimeout(timer);
    }
  }, [show, onClose]);

  const config = toastConfig[type] || toastConfig.error;
  const Icon = config.icon;

  return (
    <div
      className={`fixed top-10 right-10 z-[100] flex transform items-center gap-3 rounded-xl border ${config.borderColor} ${config.bgColor} p-4 shadow-2xl transition-all duration-300 ${
        show
          ? "translate-x-0 opacity-100"
          : "pointer-events-none translate-x-10 opacity-0"
      }`}
    >
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${config.iconBg} ${config.iconColor}`}>
        <Icon className="h-6 w-6" />
      </div>
      <div className="max-w-[320px]">
        <p className="text-sm font-bold text-slate-900">
          {title || (type === 'error' ? 'Ошибка' : 'Уведомление')}
        </p>
        <p className="mt-1 text-xs text-slate-600 leading-relaxed">
          {message}
        </p>
      </div>
      <button
        onClick={onClose}
        className="ml-2 text-slate-400 hover:text-slate-600"
      >
        <X size={16} />
      </button>
    </div>
  );
};
