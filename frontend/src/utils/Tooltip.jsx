import { useLayoutEffect, useRef, useState } from "react";

/** Показывает подсказку при необходимости, проверяя фактическое обрезание текста */
export const Tooltip = ({
  children,
  text,
  minLength = 20,
  overflowOnly = false,
}) => {
  const wrapperRef = useRef(null);
  const [truncated, setTruncated] = useState(false);
  const measure = () => {
    const target = wrapperRef.current?.querySelector(".truncate");
    setTruncated(
      !!target &&
        target.clientWidth > 0 &&
        target.scrollWidth > target.clientWidth,
    );
  };
  useLayoutEffect(() => {
    if (!overflowOnly) return;
    const target = wrapperRef.current?.querySelector(".truncate");
    if (!target) return;
    const check = () =>
      setTruncated(
        target.clientWidth > 0 && target.scrollWidth > target.clientWidth,
      );
    check();
    const observer = new ResizeObserver(check);
    observer.observe(target);
    return () => observer.disconnect();
  }, [overflowOnly, text, children]);

  if (!text || text === "—" || (!overflowOnly && text.length < minLength)) {
    return <div className="w-full">{children}</div>;
  }

  return (
    <div
      ref={wrapperRef}
      onMouseEnter={overflowOnly ? measure : undefined}
      className="group/tooltip relative w-full min-w-0"
    >
      {children}

      {(!overflowOnly || truncated) && (
        <div className="pointer-events-none invisible absolute bottom-full left-0 z-[110] mb-2 w-max max-w-[320px] rounded-lg bg-slate-800 px-3 py-2 text-xs font-normal text-white opacity-0 shadow-2xl transition-all duration-200 group-hover/tooltip:visible group-hover/tooltip:opacity-100">
          {text}
          <div className="absolute top-full left-4 -mt-1 border-4 border-transparent border-t-slate-800"></div>
        </div>
      )}
    </div>
  );
};
