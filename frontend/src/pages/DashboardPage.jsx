import React, { useState, useEffect, useMemo } from "react";
import {
  Filter,
  Plus,
  ArrowUpDown,
  X,
  Settings,
  Download,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

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
} from "../hooks/api/index";
import { useDebouncedValue } from "../hooks/useDebounce";
import { exportCasesToExcel } from "../api/export";

export default React.memo(function DashboardPage() {
  const navigate = useNavigate();

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

  // --- СОСТОЯНИЯ ФИЛЬТРОВ ---
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [appliedFilters, setAppliedFilters] = useState(INITIAL_FILTERS);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const { user: currentUser } = useAuth();

  // Debounced фильтры для оптимизации
  const debouncedAppliedFilters = useDebouncedValue(appliedFilters, 300);

  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedAppliedFilters, sortOrder]);

  // React Query хуки
  const {
    data: casesData = { items: [], total: 0 },
    isLoading: loading,
    error: listError,
  } = useCasesList(
    debouncedAppliedFilters,
    sortOrder,
    currentPage,
    itemsPerPage,
  );
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
    setSelectedCaseIndex(caseItem.display_number);
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

  // Функция экспорта
  const handleExport = async () => {
    try {
      setIsExporting(true);
      await exportCasesToExcel(appliedFilters);
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
          <div className="flex items-center gap-3">
            {/* Кнопка фильтров */}
            <button
              onClick={() => setIsFilterOpen(true)}
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
          </div>

          {/* Счётчик */}
          <p className="px-1 text-[12px] font-bold text-slate-600 uppercase">
            Всего записей:{" "}
            <span className="font-black text-indigo-600">{totalCount}</span>
          </p>
        </div>

        {/* ПРАВЫЙ БЛОК КНОПОК */}
        <div className="flex items-center gap-3">
          {/* Кнопка экспорта в Excel */}
          <button
            onClick={handleExport}
            disabled={isExporting}
            className={`flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-black tracking-wider uppercase shadow-sm transition-all active:scale-95 ${
              isExporting
                ? "cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400"
                : "border-green-200 bg-green-50 text-green-600 hover:border-green-300 hover:bg-green-100"
            }`}
          >
            {isExporting ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-green-600 border-t-transparent"></div>
            ) : (
              <Download className="h-4 w-4" />
            )}
            {isExporting ? "Экспорт..." : "Экспорт в Excel"}
          </button>

          {/* Кнопка управления оборудованием (только для superadmin) */}
          {currentUser?.role === "superadmin" && (
            <button
              onClick={() => navigate("/equipment-management")}
              className="flex items-center justify-center gap-2 rounded-xl border border-purple-200 bg-purple-50 px-4 py-2.5 text-xs font-black tracking-wider text-purple-600 uppercase shadow-sm transition-all hover:border-purple-300 hover:bg-purple-100 active:scale-95"
            >
              <Settings className="h-4 w-4" />
              Оборудование
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
                        className="h-8 w-12 rounded-lg border-2 border-indigo-400 bg-white px-1 text-center text-xs font-bold text-indigo-700 shadow-sm outline-none focus:ring-0"
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
