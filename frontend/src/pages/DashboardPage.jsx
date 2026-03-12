import React, { useState, useEffect, useMemo } from "react";
import { Filter, Plus, ArrowUpDown, X } from "lucide-react";

// Компоненты
import { RepairCaseList } from "../components/RepairCaseList";
import { RepairCaseDetails } from "../components/RepairCaseDetails";
import { FilterSidebar } from "../components/FilterSidebar";
import { CreateRepairCase } from "../components/CreateRepairCase";

// Утилиты и Константы
import { INITIAL_FILTERS } from "../constants/filters";
import { countActiveFilters } from "../utils/filterUtils";
import { useAuth } from "../context/AuthContext";
import { logger } from "../utils/logger";
import {
  useCasesList,
  useCaseDetail,
  useUpdateCase,
  useDeleteCase,
  useFilterOptions,
  useAllCasesForNumbering,
} from "../hooks/api/index";
import { useDebouncedValue } from "../hooks/useDebounce";

export default React.memo(function DashboardPage() {
  // --- СОСТОЯНИЯ СПИСКА ---
  const [sortOrder, setSortOrder] = useState("desc");
  const [selectedCase, setSelectedCase] = useState(null);
  const [selectedCaseIndex, setSelectedCaseIndex] = useState(null);
  const [loadingText, setLoadingText] = useState("Загрузка карточки...");
  const [loadingDetail, setLoadingDetail] = useState(false);

  // --- СОСТОЯНИЯ ФИЛЬТРОВ ---
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [appliedFilters, setAppliedFilters] = useState(INITIAL_FILTERS);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { user: currentUser } = useAuth();

  // Debounced фильтры для оптимизации
  const debouncedAppliedFilters = useDebouncedValue(appliedFilters, 300);

  // React Query хуки
  const {
    data: cases = [],
    isLoading: loading,
    error: listError,
  } = useCasesList(debouncedAppliedFilters, sortOrder);

  const { data: allCasesForNumbering = [] } = useAllCasesForNumbering();
  const {
    data: selectedCaseDetail,
    isLoading: loadingDetailFromQuery,
    error: detailError,
  } = useCaseDetail(selectedCase?.id);
  const updateCaseMutation = useUpdateCase();
  const deleteCaseMutation = useDeleteCase();

  const { data: filterOptions } = useFilterOptions();

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

  const handleCaseUpdate = (updated) => {
    updateCaseMutation.mutate({
      caseId: updated.id,
      data: updated,
    });
    logger.log("Случай обновляется:", updated.id);
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

  const handleCaseClick = async (caseItem) => {
    setSelectedCaseIndex(caseItem.displayNumber);
    setSelectedCase(caseItem);
    logger.log("Выбран случай:", caseItem.id);
  };

  const handleApplyFilters = (newFilters) => {
    setAppliedFilters(newFilters);
  };

  const handleClearAllFilters = () => {
    setAppliedFilters(INITIAL_FILTERS);
  };

  const activeCount = countActiveFilters(appliedFilters);

  // ЛОГИКА АБСОЛЮТНОЙ НУМЕРАЦИИ
  const idToAbsoluteNumber = useMemo(() => {
    return new Map(
      [...allCasesForNumbering]
        .sort((a, b) => a.id - b.id)
        .map((caseItem, index) => [caseItem.id, index + 1]),
    );
  }, [allCasesForNumbering]);

  // ЛОГИКА СОРТИРОВКИ
  const sortedCases = useMemo(() => {
    const casesWithAbsoluteNumbers = cases.map((caseItem) => ({
      ...caseItem,
      displayNumber: idToAbsoluteNumber.get(caseItem.id) || caseItem.id,
    }));

    return [...casesWithAbsoluteNumbers].sort((a, b) => {
      if (sortOrder === "desc") {
        return b.id - a.id;
      } else {
        return a.id - b.id;
      }
    });
  }, [cases, idToAbsoluteNumber, sortOrder]);

  return (
    <div className="flex h-full flex-col gap-2 overflow-hidden">
      {/* HEADER: Кнопка фильтров, сортировка, счетчик и кнопка создания */}
      <div className="flex w-full flex-shrink-0 items-end justify-between px-4 py-2 md:px-3">
        <div className="flex flex-col gap-2">
          {/* БЛОК КНОПОК */}
          <div className="flex items-center gap-3">
            {/* Кнопка фильтров */}
            <button
              onClick={() => setIsFilterOpen(true)}
              className={`flex items-center justify-center gap-2 rounded-xl border px-4 py-2 text-xs font-black tracking-wider uppercase shadow-sm transition-all active:scale-95 ${
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
                className="flex items-center justify-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-[11px] font-black tracking-wider text-red-600 uppercase shadow-sm transition-all hover:border-red-300 hover:bg-red-100 active:scale-95"
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
              className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-black tracking-wider text-slate-600 uppercase shadow-sm transition-all hover:border-slate-300 hover:bg-slate-50 active:scale-95"
            >
              <ArrowUpDown className="h-3 w-3 text-slate-500" />
              {sortOrder === "desc" ? "Сначала новые" : "Сначала старые"}
            </button>
          </div>

          {/* Счётчик */}
          <p className="px-1 text-[12px] font-bold text-slate-600 uppercase">
            Всего записей:{" "}
            <span className="font-black text-indigo-600">{cases.length}</span>
          </p>
        </div>

        {/* Кнопка создания */}
        {currentUser?.role !== "viewer" && (
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-black tracking-widest text-white uppercase shadow-lg shadow-indigo-100 transition-all hover:bg-indigo-700 hover:shadow-indigo-200 active:scale-95"
          >
            <Plus className="h-4 w-4 stroke-[3px]" />
            Создать
          </button>
        )}
      </div>

      {/* ОСНОВНОЙ СПИСОК */}
      <div className="min-h-0 flex-1">
        {loading && cases.length === 0 ? (
          <div className="flex h-64 animate-pulse flex-col items-center justify-center gap-4">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
            <span className="text-xs font-black tracking-widest text-slate-400 uppercase">
              Синхронизация данных...
            </span>
          </div>
        ) : (
          <RepairCaseList cases={sortedCases} onCaseClick={handleCaseClick} />
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
          caseIndex={selectedCase?.displayNumber || selectedCaseIndex}
          onUpdate={handleCaseUpdate}
          onDelete={handleCaseDelete}
          setLoadingDetail={setLoadingDetail}
          setLoadingText={setLoadingText}
        />
      )}

      {/* САЙДБАР ФИЛЬТРОВ */}
      <FilterSidebar
        isOpen={isFilterOpen}
        onClose={() => setIsFilterOpen(false)}
        appliedFilters={appliedFilters}
        onApply={handleApplyFilters}
        options={enhancedFilterOptions}
      />
    </div>
  );
});
