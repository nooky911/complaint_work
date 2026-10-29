import React, { lazy, Suspense, useState, useEffect, useMemo } from "react";
import {
  Filter,
  Plus,
  ArrowUpDown,
  X,
  Download,
  ChevronLeft,
  ChevronRight,
  Search,
} from "lucide-react";

// Компоненты
import { RepairCaseList } from "../components/RepairCaseList";
import { SectionsMenu } from "../components/Layout/SectionsMenu";

// Утилиты и Константы
import { INITIAL_FILTERS } from "../constants/filters";
import { countActiveFilters } from "../utils/filterUtils";
import { useAuth } from "../context/AuthContext";
import { logger } from "../utils/logger";
import {
  useCasesList,
  useCaseDisplayNumbers,
  useCaseDetail,
  useUpdateCase,
  useDeleteCase,
  useFilterOptions,
} from "../hooks/api/index";
import { useDebouncedValue } from "../hooks/useDebounce";
import { useDropdown } from "../hooks/useDropdown";

// Загружаем формы и фильтры при первом открытии
const RepairCaseDetails = lazy(() =>
  import("../components/RepairCaseDetails").then((module) => ({
    default: module.RepairCaseDetails,
  })),
);
const CreateRepairCase = lazy(() =>
  import("../components/CreateRepairCase").then((module) => ({
    default: module.CreateRepairCase,
  })),
);
const FilterSidebar = lazy(() =>
  import("../components/FilterSidebar").then((module) => ({
    default: module.FilterSidebar,
  })),
);

/** Показывает загрузку окна, пока браузер получает его код */
function WindowLoading() {
  return (
    <div
      role="status"
      className="fixed inset-0 z-[110] flex items-center justify-center bg-black/10 backdrop-blur-sm"
    >
      <div className="flex items-center gap-3 rounded-xl bg-white p-6 text-sm font-bold text-slate-900 shadow-lg">
        <div
          aria-hidden="true"
          className="h-6 w-6 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"
        />
        Загрузка окна…
      </div>
    </div>
  );
}

export default React.memo(function DashboardPage() {
  const { user: currentUser } = useAuth();
  const restricted = !!currentUser?.restricted_access;
  const filtersStorageKey = restricted
    ? `restrictedFilters:${currentUser.id}`
    : "appliedFilters";
  // --- ПАГИНАЦИЯ ---
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 25;
  const [isEditingPage, setIsEditingPage] = useState(false);
  const [pageInput, setPageInput] = useState("");

  // --- СОСТОЯНИЯ СПИСКА ---
  const [sortOrder, setSortOrder] = useState("desc");
  const [selectedCase, setSelectedCase] = useState(null);
  const [selectedCaseIndex, setSelectedCaseIndex] = useState(null);
  const [loadingText, setLoadingText] = useState("Загрузка карточки...");
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [quickCaseNumber, setQuickCaseNumber] = useState(null);
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
  );
  const numberSearchPending = caseNumberInput !== debouncedCaseNumberInput;
  const candidateNumber =
    draftCaseNumber ??
    (!numberSearchPending &&
    numberChoices.data?.includes(Number(caseNumberInput))
      ? Number(caseNumberInput)
      : null);

  // --- СОСТОЯНИЯ ФИЛЬТРОВ ---
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [filterLoaded, setFilterLoaded] = useState(false);
  const [appliedFilters, setAppliedFilters] = useState(() => {
    const saved = localStorage.getItem(filtersStorageKey);
    return saved ? JSON.parse(saved) : INITIAL_FILTERS;
  });

  // Сохраняем фильтры в localStorage при изменении
  useEffect(() => {
    localStorage.setItem(filtersStorageKey, JSON.stringify(appliedFilters));
  }, [appliedFilters, filtersStorageKey]);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Debounced фильтры для оптимизации
  const debouncedAppliedFilters = useDebouncedValue(appliedFilters, 300);
  const effectiveFilters = useMemo(
    () =>
      quickCaseNumber
        ? { display_number: quickCaseNumber }
        : debouncedAppliedFilters,
    [quickCaseNumber, debouncedAppliedFilters],
  );

  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedAppliedFilters, sortOrder, quickCaseNumber]);

  // React Query хуки
  const {
    data: casesData = { items: [], total: 0 },
    isLoading: loading,
    error: listError,
  } = useCasesList(effectiveFilters, sortOrder, currentPage, itemsPerPage);
  const cases = casesData.items || [];
  const totalCount = casesData.total || 0;
  const totalPages = Math.ceil(totalCount / itemsPerPage) || 1;

  const {
    data: selectedCaseDetail,
    isLoading: loadingDetailFromQuery,
    error: detailError,
  } = useCaseDetail(selectedCase?.id);
  const updateCaseMutation = useUpdateCase();
  const deleteCaseMutation = useDeleteCase();

  const {
    data: filterOptions,
    isPending: filterOptionsLoading,
    isError: filterOptionsError,
    refetch: refetchFilterOptions,
  } = useFilterOptions(filterLoaded);

  const enhancedFilterOptions = useMemo(() => {
    if (!filterOptions) return null;

    return { ...filterOptions };
  }, [filterOptions]);

  // --- ОБРАБОТЧИКИ ---
  useEffect(() => {
    if (listError) {
      logger.error("Ошибка загрузки списка случаев:", listError);
    }
    if (detailError) {
      logger.error("Ошибка загрузки деталей случая:", detailError);
    }
  }, [listError, detailError]);

  const handleCaseUpdate = (payload) => {
    updateCaseMutation.mutate({
      caseId: selectedCase.id,
      data: payload,
    });
    logger.log("Случай обновляется:", selectedCase.id);
  };

  const handleCaseDelete = (deletedId) => {
    try {
      deleteCaseMutation.mutate(deletedId, {
        onSuccess: () => {
          setSelectedCase(null);
          setSelectedCaseIndex(null);
          logger.log("Случай успешно удален:", deletedId);
        },
        onError: (error) => {
          logger.error("Ошибка удаления случая:", error);
        },
      });
    } catch (error) {
      logger.error("Ошибка удаления случая:", error);
    }
  };

  const handleCaseClick = React.useCallback(async (caseItem) => {
    setSelectedCaseIndex(caseItem.display_number);
    setSelectedCase(caseItem);
    logger.log("Выбран случай:", caseItem.id);
  }, []);

  const handleApplyFilters = (newFilters) => {
    setQuickCaseNumber(null);
    setAppliedFilters(newFilters);
  };

  const handleClearAllFilters = () => {
    setQuickCaseNumber(null);
    setAppliedFilters(INITIAL_FILTERS);
  };

  const activeCount = quickCaseNumber ? 0 : countActiveFilters(appliedFilters);

  // Функция экспорта
  const handleExport = async () => {
    try {
      setIsExporting(true);
      const { exportCasesToExcel } = await import("../api/export");
      await exportCasesToExcel(
        quickCaseNumber ? { display_number: quickCaseNumber } : appliedFilters,
      );
    } catch (error) {
      logger.log("Экспорт завершен с ошибкой:", error.message);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex h-full flex-col gap-2 overflow-hidden">
      {/* HEADER: Кнопка фильтров, сортировка, счетчик и кнопка создания */}
      <div className="flex w-full flex-shrink-0 items-start justify-between px-4 pt-2 md:px-3">
        <div className="flex flex-col gap-2">
          {/* БЛОК КНОПОК */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Кнопка фильтров */}
            <button
              onClick={() => {
                setFilterLoaded(true);
                setIsFilterOpen(true);
              }}
              className={`flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-black tracking-wider uppercase shadow-sm transition-all active:scale-95 ${
                activeCount > 0
                  ? "border-indigo-600 bg-indigo-600 text-white shadow-indigo-200"
                  : "border-indigo-100 bg-indigo-50 text-indigo-600 hover:border-indigo-200 hover:bg-indigo-100"
              }`}
            >
              <Filter
                className={`h-3 w-3 ${activeCount > 0 ? "fill-white" : "fill-indigo-500"}`}
              />
              Параметры поиска
              {activeCount > 0 && (
                <span className="ml-1 flex h-4 w-4 items-center justify-center rounded-full bg-white text-[9px] font-black text-indigo-600">
                  {activeCount}
                </span>
              )}
            </button>

            {/* Кнопка очистки фильтров */}
            {activeCount > 0 && (
              <button
                onClick={handleClearAllFilters}
                className="flex items-center justify-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-[11px] font-black tracking-wider text-red-600 uppercase shadow-sm transition-all hover:border-red-300 hover:bg-red-100 active:scale-95"
                title="Сбросить все фильтры"
              >
                <X className="h-3.5 w-3.5" />
                Очистить
              </button>
            )}
            {/* Кнопка сортировки */}
            <button
              onClick={() =>
                setSortOrder((prev) => (prev === "desc" ? "asc" : "desc"))
              }
              className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-black tracking-wider text-slate-600 uppercase shadow-sm transition-all hover:border-slate-300 hover:bg-slate-50 active:scale-95"
            >
              <ArrowUpDown className="h-4 w-4 text-slate-500" />
              {sortOrder === "desc" ? "Сначала новые" : "Сначала старые"}
            </button>

            {/* Кнопка поиска случая по его номеру */}
            <div
              className="relative flex items-center gap-1"
              ref={numberSearchRef}
            >
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
                    setQuickCaseNumber(null);
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
                    setCurrentPage(1);
                    setQuickCaseNumber(candidateNumber);
                    setNumberSearchOpen(false);
                  }}
                  className="absolute top-full left-0 z-50 mt-2 w-64 max-w-[calc(100vw-2rem)] rounded-xl border border-slate-300 bg-white p-3 shadow-xl"
                >
                  <label
                    htmlFor="dashboard-case-number"
                    className="mb-2 block text-xs font-bold text-slate-600"
                  >
                    Номер случая в списке
                  </label>
                  <input
                    id="dashboard-case-number"
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
          </div>

          {/* Счётчик */}
          <p className="px-1 text-[12px] font-bold text-slate-600 uppercase">
            Всего записей:{" "}
            <span className="font-black text-indigo-600">{totalCount}</span>
          </p>
        </div>

        {/* ПРАВЫЙ БЛОК КНОПОК */}
        <div className="flex items-center gap-3">
          {!restricted && (
            <SectionsMenu isSuperadmin={currentUser?.role === "superadmin"} />
          )}

          {/* Кнопка экспорта в Excel */}
          {!restricted && (
            <button
              onClick={handleExport}
              disabled={isExporting}
              className={`flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-black tracking-wider uppercase shadow-sm transition-all active:scale-95 ${
                isExporting
                  ? "cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400"
                  : "border-green-200 bg-green-50 text-green-700 hover:border-green-300 hover:bg-green-100"
              }`}
            >
              {isExporting ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-green-700 border-t-transparent"></div>
              ) : (
                <Download className="h-4 w-4" />
              )}
              {isExporting ? "Экспорт..." : "Экспорт в Excel"}
            </button>
          )}

          {/* Кнопка создания */}
          {currentUser?.role !== "viewer" && (
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="flex items-center gap-2 rounded-xl bg-[#0064fe] px-4 py-2.5 text-xs font-black tracking-wider text-white uppercase antialiased shadow-lg shadow-indigo-100 transition-all hover:bg-[#0052cc] hover:shadow-indigo-200 active:scale-95"
            >
              <Plus className="h-4 w-4 stroke-[3px]" />
              Создать
            </button>
          )}
        </div>
      </div>

      {/* ОСНОВНОЙ СПИСОК И ПАГИНАЦИЯ */}
      <div className="flex min-h-0 flex-1 flex-col">
        {loading && cases.length === 0 ? (
          <div className="flex h-64 animate-pulse flex-col items-center justify-center gap-4">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
            <span className="text-xs font-black tracking-widest text-slate-400 uppercase">
              Синхронизация данных...
            </span>
          </div>
        ) : (
          <RepairCaseList
            cases={cases}
            restricted={restricted}
            onCaseClick={handleCaseClick}
            pagination={
              <div className="flex w-fit items-center gap-1 p-1 select-none">
                {/* Кнопка Назад */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setCurrentPage((p) => Math.max(1, p - 1));
                  }}
                  disabled={currentPage === 1}
                  aria-label="Предыдущая страница"
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-slate-200/60 disabled:opacity-30 disabled:hover:bg-transparent"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>

                {/* Цифры страниц */}
                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setCurrentPage(1);
                    }}
                    className={`h-8 min-w-[2rem] rounded-lg px-2 text-xs font-black transition-colors ${
                      currentPage === 1
                        ? "bg-indigo-600 text-white shadow-md"
                        : "text-slate-600 hover:bg-slate-200/60"
                    }`}
                  >
                    1
                  </button>

                  {currentPage > 3 && (
                    <span className="flex h-8 w-6 items-center justify-center text-xs tracking-widest text-slate-400">
                      ...
                    </span>
                  )}

                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                    (p) => {
                      if (
                        p > 1 &&
                        p < totalPages &&
                        p >= currentPage - 1 &&
                        p <= currentPage + 1
                      ) {
                        return (
                          <button
                            key={p}
                            onClick={(e) => {
                              e.stopPropagation();
                              setCurrentPage(p);
                            }}
                            className={`h-8 min-w-[2rem] rounded-lg px-2 text-xs font-black transition-colors ${
                              currentPage === p
                                ? "bg-indigo-600 text-white shadow-md"
                                : "text-slate-600 hover:bg-slate-200/60"
                            }`}
                          >
                            {p}
                          </button>
                        );
                      }
                      return null;
                    },
                  )}

                  {/* Ручной ввод страниц */}
                  {currentPage < totalPages - 2 &&
                    (isEditingPage ? (
                      <input
                        type="number"
                        autoFocus
                        placeholder="№"
                        className="h-8 w-12 rounded-lg border-2 border-indigo-400 bg-white px-1 text-center text-sm font-bold text-slate-900 shadow-sm outline-none focus:ring-0"
                        value={pageInput}
                        onChange={(e) => setPageInput(e.target.value)}
                        onBlur={() => setIsEditingPage(false)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            const p = parseInt(pageInput, 10);
                            if (p > 0 && p <= totalPages) setCurrentPage(p);
                            setIsEditingPage(false);
                            setPageInput("");
                          }
                        }}
                      />
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setPageInput("");
                          setIsEditingPage(true);
                        }}
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-xs font-black tracking-widest text-slate-400 transition-colors hover:bg-slate-200/60 hover:text-indigo-600"
                        title="Ввести номер страницы..."
                      >
                        ...
                      </button>
                    ))}

                  {totalPages > 1 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setCurrentPage(totalPages);
                      }}
                      className={`h-8 min-w-[2rem] rounded-lg px-2 text-xs font-black transition-colors ${
                        currentPage === totalPages
                          ? "bg-indigo-600 text-white shadow-md"
                          : "text-slate-600 hover:bg-slate-200/60"
                      }`}
                    >
                      {totalPages}
                    </button>
                  )}
                </div>

                {/* Кнопка Вперед */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setCurrentPage((p) => Math.min(totalPages, p + 1));
                  }}
                  disabled={currentPage === totalPages}
                  aria-label="Следующая страница"
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-slate-200/60 disabled:opacity-30 disabled:hover:bg-transparent"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </div>
            }
          />
        )}
      </div>

      {/* ЛОАДЕР ДЕТАЛЕЙ */}
      {(loadingDetail || loadingDetailFromQuery) && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/10 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-4 rounded-2xl bg-white p-8 shadow-2xl">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
            <span className="text-sm font-bold tracking-tight text-slate-800 uppercase">
              {loadingText}
            </span>
          </div>
        </div>
      )}

      <Suspense fallback={<WindowLoading />}>
        {isCreateModalOpen && (
          <CreateRepairCase
            currentUser={currentUser}
            onClose={() => setIsCreateModalOpen(false)}
            onCreated={() => {
              setIsCreateModalOpen(false);
            }}
          />
        )}

        {/* МОДАЛЬНОЕ ОКНО ДЕТАЛЕЙ */}
        {selectedCase && (
          <RepairCaseDetails
            currentUser={currentUser}
            repairCase={selectedCaseDetail || selectedCase}
            onClose={() => {
              setSelectedCase(null);
            }}
            caseIndex={selectedCase?.display_number || selectedCaseIndex}
            onUpdate={handleCaseUpdate}
            onDelete={handleCaseDelete}
            setLoadingDetail={setLoadingDetail}
            setLoadingText={setLoadingText}
          />
        )}

        {/* САЙДБАР ФИЛЬТРОВ */}
        {filterLoaded && (
          <FilterSidebar
            restricted={restricted}
            isOpen={isFilterOpen}
            onClose={() => setIsFilterOpen(false)}
            appliedFilters={appliedFilters}
            onApply={handleApplyFilters}
            options={enhancedFilterOptions}
            optionsLoading={filterOptionsLoading}
            optionsError={filterOptionsError}
            onRetryOptions={refetchFilterOptions}
          />
        )}
      </Suspense>
    </div>
  );
});
