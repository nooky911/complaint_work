import { ArrowLeft } from "lucide-react";

/** Общая шапка раздела с кнопкой возврата и дополнительными действиями */
export function SectionPageHeader({ title, onBack, children }) {
  return (
    <header className="flex min-h-[60px] shrink-0 flex-wrap items-center gap-4 border-b border-gray-200 bg-white px-6 py-2 [&>button]:self-center">
      <button
        type="button"
        onClick={onBack}
        className="flex items-center gap-2 text-gray-600 transition-colors hover:text-gray-900"
      >
        <ArrowLeft className="h-5 w-5" />
        <span>Назад</span>
      </button>
      <h1 className="mr-auto text-xl font-semibold text-gray-900">{title}</h1>
      {children}
    </header>
  );
}
