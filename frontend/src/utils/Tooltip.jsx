import React from "react";

export const Tooltip = ({ children, text, minLength = 20 }) => {
  if (!text || text === "—" || text.length < minLength) {
    return <div className="w-full">{children}</div>;
  }

  return (
    <div className="group relative w-full">
      {children}

      <div className="pointer-events-none invisible absolute bottom-full left-0 z-[110] mb-2 w-max max-w-[320px] rounded-lg bg-slate-800 px-3 py-2 text-xs font-normal text-white opacity-0 shadow-2xl transition-all duration-200 group-hover:visible group-hover:opacity-100">
        {text}
        <div className="absolute top-full left-4 -mt-1 border-4 border-transparent border-t-slate-800"></div>
      </div>
    </div>
  );
};
