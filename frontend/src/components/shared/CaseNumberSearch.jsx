import { useId, useState } from "react";
import { Search, X } from "lucide-react";
import { useDropdown } from "../../hooks/useDropdown";
import { useDebouncedValue } from "../../hooks/useDebounce";
import { useCaseDisplayNumbers } from "../../hooks/api/index.jsx";

/** Общий выпадающий поиск по номеру случая с выбором, отменой и подтверждением */
export function CaseNumberSearch({
  value: quickCaseNumber,
  onChange,
  direction = "loco",
}) {
  const inputId = useId();
  const [caseNumberInput, setCaseNumberInput] = useState("");
  const [draftCaseNumber, setDraftCaseNumber] = useState(null);
  const {
    isOpen: isNumberSearchOpen,
    setIsOpen: setNumberSearchOpen,
    containerRef: numberSearchRef,
  } = useDropdown();
  const debouncedCaseNumberInput = useDebouncedValue(caseNumberInput, 250);
  const numberChoices = useCaseDisplayNumbers(
    debouncedCaseNumberInput,
    isNumberSearchOpen,
    direction,
  );
  const numberSearchPending = caseNumberInput !== debouncedCaseNumberInput;
  const candidateNumber =
    draftCaseNumber ??
    (!numberSearchPending &&
    numberChoices.data?.includes(Number(caseNumberInput))
      ? Number(caseNumberInput)
      : null);

  return (
    <>
      {/* Кнопка поиска случая по его номеру */}
      <div className="relative flex items-center gap-1" ref={numberSearchRef}>
        <button
          type="button"
          onClick={() => {
            if (!isNumberSearchOpen) {
              setCaseNumberInput(
                quickCaseNumber ? String(quickCaseNumber) : "",
              );
              setDraftCaseNumber(quickCaseNumber);
            }
            setNumberSearchOpen(!isNumberSearchOpen);
          }}
          aria-expanded={isNumberSearchOpen}
          className={`flex items-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-black tracking-wider uppercase shadow-sm transition-colors ${
            quickCaseNumber
              ? "border-indigo-600 bg-indigo-600 text-white"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
          }`}
        >
          <Search className="h-4 w-4" />
          {quickCaseNumber ? `Случай №${quickCaseNumber}` : "№ случая"}
        </button>
        {quickCaseNumber && (
          <button
            type="button"
            title="Сбросить поиск по номеру"
            aria-label="Сбросить поиск по номеру"
            onClick={() => {
              onChange(null);
              setNumberSearchOpen(false);
            }}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        )}
        {isNumberSearchOpen && (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!candidateNumber) return;
              onChange(candidateNumber);
              setNumberSearchOpen(false);
            }}
            className="absolute top-full left-0 z-50 mt-2 w-64 max-w-[calc(100vw-2rem)] rounded-xl border border-slate-300 bg-white p-3 shadow-xl"
          >
            <label
              htmlFor={inputId}
              className="mb-2 block text-xs font-bold text-slate-600"
            >
              Номер случая в списке
            </label>
            <input
              id={inputId}
              type="text"
              inputMode="numeric"
              autoFocus
              autoComplete="off"
              maxLength={10}
              value={caseNumberInput}
              placeholder="Введите номер"
              onChange={(event) => {
                setCaseNumberInput(event.target.value.replace(/\D/g, ""));
                setDraftCaseNumber(null);
              }}
              onKeyDown={(event) => {
                if (event.key === "Escape") setNumberSearchOpen(false);
              }}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-bold text-slate-900 outline-none focus:border-indigo-500"
            />
            <div className="mt-2 max-h-48 overflow-y-auto">
              {numberChoices.isFetching || numberSearchPending ? (
                <p className="py-3 text-center text-xs text-slate-500">
                  Загрузка…
                </p>
              ) : numberChoices.isError ? (
                <button
                  type="button"
                  onClick={() => numberChoices.refetch()}
                  className="py-3 text-xs text-red-700"
                >
                  Ошибка загрузки. Повторить
                </button>
              ) : numberChoices.data?.length ? (
                numberChoices.data.map((number) => (
                  <button
                    key={number}
                    type="button"
                    onClick={() => {
                      setDraftCaseNumber(number);
                      setCaseNumberInput(String(number));
                    }}
                    className={`block w-full rounded-lg px-3 py-2 text-left text-sm font-bold ${candidateNumber === number ? "bg-indigo-100 text-indigo-800" : "text-slate-700 hover:bg-slate-50"}`}
                  >
                    {number}
                  </button>
                ))
              ) : (
                <p className="py-3 text-center text-xs text-slate-500">
                  Такого номера нет
                </p>
              )}
            </div>
            <div className="mt-3 flex justify-end gap-2 border-t border-slate-100 pt-3">
              <button
                type="button"
                onClick={() => setNumberSearchOpen(false)}
                className="rounded-lg px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                Отмена
              </button>
              <button
                type="submit"
                disabled={!candidateNumber}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                ОК
              </button>
            </div>
          </form>
        )}
      </div>
    </>
  );
}
