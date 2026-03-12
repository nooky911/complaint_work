import { ChevronDown } from "lucide-react";

export const FilterSection = ({
  title,
  icon: Icon,
  isOpen,
  onToggle,
  children,
  activeCount,
  colorTheme = {
    border: "border-slate-200",
    bgGradient: "from-slate-50",
    iconBg: "bg-slate-600",
    iconText: "text-slate-500",
    titleText: "text-slate-700",
  },
}) => {
  return (
    <div className="space-y-1">
      <div
        onClick={onToggle}
        className={`relative mb-3 flex cursor-pointer items-center justify-between rounded-lg border ${colorTheme.border} bg-gradient-to-r ${colorTheme.bgGradient} to-white px-3 py-2 shadow-sm transition-colors hover:brightness-95`}
      >
        <div className="flex items-center gap-2">
          <div
            className={`absolute top-0 bottom-0 left-0 w-1 rounded-l-lg ${colorTheme.iconBg}`}
          ></div>
          <Icon className={`h-4 w-4 ${colorTheme.iconText}`} />
          <h4
            className={`text-xs font-bold tracking-wider uppercase ${colorTheme.titleText}`}
          >
            {title}
          </h4>

          {activeCount > 0 && (
            <span className="ml-1 flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 text-[9px] font-black text-white shadow-sm ring-1 ring-white">
              {activeCount}
            </span>
          )}
        </div>
        <ChevronDown
          className={`h-4 w-4 ${colorTheme.iconText} transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </div>

      {isOpen && (
        <div className="animate-in slide-in-from-top-2 fade-in space-y-3 rounded-2xl border border-slate-200 bg-slate-200/50 p-3 shadow-sm duration-200">
          {children}
        </div>
      )}
    </div>
  );
};
