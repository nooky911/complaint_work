import React from "react";
import { Building2, UserCheck, Calendar, X } from "lucide-react";
import { getText, formatFullName, formatDate } from "../../utils/formatters";

export const CaseHeader = ({
  repairCase,
  displayId,
  status,
  isEditing,
  references,
  editData,
  onClose,
  currentUser,
  users,
  updateField,
}) => {
  const StatusIcon = status?.icon;

  return (
    <div className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-2">
      <div className="flex items-center gap-4">
        <span className="text-[16px] font-black tracking-tight text-slate-800">
          #{displayId}
        </span>
        {status && (
          <div
            className={`flex items-center gap-2 rounded-lg px-3 py-1 text-[11px] font-bold tracking-wide uppercase shadow-sm ${status.style}`}
          >
            {StatusIcon && <StatusIcon className="h-4 w-4" />}
            {repairCase.status || repairCase.calculated_status || "Неизвестно"}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* БЛОК ПОСТАВЩИКА */}
        <div className="flex items-center gap-3 rounded-lg border-2 border-violet-300 bg-gradient-to-r from-violet-100 to-fuchsia-100 px-2 py-1 shadow-sm">
          <Building2 className="h-5 w-5 text-violet-600" />
          <div className="flex flex-col">
            <p className="text-[9px] leading-none font-bold tracking-widest text-slate-400 uppercase">
              Поставщик
            </p>
            <p className="mt-0.5 text-[13px] leading-tight font-black text-slate-700 uppercase">
              {isEditing
                ? references?.suppliers?.find(
                    (s) => s.id === editData?.supplier_id,
                  )?.name || "—"
                : getText(repairCase.supplier)}
            </p>
          </div>
        </div>

        {/* ФИО И ДАТА */}
        <div className="flex flex-col items-start justify-center gap-1 border-l border-gray-100 pl-4">
          {/* ФИО / ВЫБОР ЮЗЕРА */}
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-600">
            <UserCheck className="h-3.5 w-3.5 text-slate-400" />

            {isEditing && currentUser?.role === "superadmin" ? (
              <div className="rounded border border-indigo-200 bg-indigo-50/50 px-1.5 py-0.5">
                <select
                  value={editData?.user_id || ""}
                  onChange={(e) =>
                    updateField(
                      "user_id",
                      e.target.value ? Number(e.target.value) : null,
                    )
                  }
                  className="cursor-pointer bg-transparent outline-none focus:ring-0"
                >
                  {users?.map((u) => (
                    <option key={u.id} value={u.id}>
                      {formatFullName(u.full_name)}{" "}
                      {u.id === currentUser?.id ? "(ВЫ)" : ""}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <span>{formatFullName(repairCase.creator_full_name)}</span>
            )}
          </div>

          {/* ДАТА */}
          <div className="flex items-center gap-1.5 text-[11px] text-gray-400">
            <Calendar className="h-3.5 w-3.5" />
            <span>от {formatDate(repairCase.date_recorded)}</span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="ml-2 rounded-full p-1 transition-colors hover:bg-gray-100"
        >
          <X className="h-5 w-5 text-gray-400" />
        </button>
      </div>
    </div>
  );
};
