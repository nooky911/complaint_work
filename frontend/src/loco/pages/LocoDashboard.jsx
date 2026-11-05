import React, { lazy, Suspense, useState, useEffect, useMemo } from "react";

// Компоненты
import { Dashboard } from "../../components/shared/Dashboard";
import { DashboardToolbar } from "../../components/shared/DashboardToolbar";

// Утилиты и Константы
import { INITIAL_FILTERS } from "../../constants/filters";
import { countActiveFilters, readSavedFilters } from "../../utils/filterUtils";
import { useAuth } from "../../context/AuthContext";
import { logger } from "../../utils/logger";
import {
  useCasesList,
  useCaseDetail,
  useUpdateCase,
  useDeleteCase,
  useFilterOptions,
} from "../../hooks/api/index";
import { useDebouncedValue } from "../../hooks/useDebounce";

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

export default React.memo(function LocoDashboard() {
  const { user } = useAuth();
  const currentUser =
    user?.direction === "train" && user?.role !== "superadmin"
      ? { ...user, role: "viewer" }
      : user;
  const restricted = !!currentUser?.restricted_access;
  const filtersStorageKey = restricted
    ? `restrictedFilters:${currentUser.id}`
    : "appliedFilters";
  // --- ПАГИНАЦИЯ ---
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 25;

  // --- СОСТОЯНИЯ СПИСКА ---
  const [sortOrder, setSortOrder] = useState("desc");
  const [selectedCase, setSelectedCase] = useState(null);
  const [selectedCaseIndex, setSelectedCaseIndex] = useState(null);
  const [loadingText, setLoadingText] = useState("Загрузка карточки...");
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [quickCaseNumber, setQuickCaseNumber] = useState(null);

  // --- СОСТОЯНИЯ ФИЛЬТРОВ ---
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [filterLoaded, setFilterLoaded] = useState(false);
  const [appliedFilters, setAppliedFilters] = useState(() =>
    readSavedFilters(filtersStorageKey),
  );

  // Сохраняем фильтры в localStorage при изменении
  useEffect(() => {
    try {
      localStorage.setItem(filtersStorageKey, JSON.stringify(appliedFilters));
    } catch (error) {
      logger.error("Не удалось сохранить фильтры", error);
    }
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
    refetch: refetchCases,
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
    return updateCaseMutation.mutateAsync({
      caseId: selectedCase.id,
      data: payload,
    });
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
      const { exportCasesToExcel } = await import("../../api/export");
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
    <Dashboard
      cases={cases}
      loading={loading}
      error={listError}
      onRetry={refetchCases}
      restricted={restricted}
      onCaseClick={handleCaseClick}
      currentPage={currentPage}
      totalPages={totalPages}
      onPageChange={setCurrentPage}
      toolbar={
        <DashboardToolbar
          activeCount={activeCount}
          onOpenFilters={() => {
            setFilterLoaded(true);
            setIsFilterOpen(true);
          }}
          handleClearAllFilters={handleClearAllFilters}
          sortOrder={sortOrder}
          onSort={() =>
            setSortOrder((prev) => (prev === "desc" ? "asc" : "desc"))
          }
          quickCaseNumber={quickCaseNumber}
          onCaseNumberChange={(number) => {
            setCurrentPage(1);
            setQuickCaseNumber(number);
          }}
          totalCount={totalCount}
          restricted={restricted}
          isSuperadmin={currentUser?.role === "superadmin"}
          handleExport={handleExport}
          isExporting={isExporting}
          canCreate={currentUser?.role !== "viewer"}
          onCreate={() => setIsCreateModalOpen(true)}
        />
      }
    >
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
    </Dashboard>
  );
});
