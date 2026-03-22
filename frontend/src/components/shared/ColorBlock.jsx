import React from "react";

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
  cyan: {
    border: "border-cyan-100",
    bgFrom: "from-cyan-50",
    bgTo: "to-white",
    accent: "bg-[#0891b2]",
    icon: "text-[#0891b2]",
    title: "text-[#0e7490]",
  },
  yellow: {
    border: "border-yellow-100",
    bgFrom: "from-yellow-50",
    bgTo: "to-white",
    accent: "bg-[#eab308]",
    icon: "text-[#ca8a04]",
    title: "text-[#a16207]",
  },
};

export function ColorBlock({
  blockTitle,
  blockIcon,
  blockColor = "blue",
  children,
}) {
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
