import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "../../api/api";
import { useCasesList } from "../../hooks/api/index.jsx";
import { trainEquipmentName } from "../utils/caseFormData";
import { useAuth } from "../../context/AuthContext";
import { Dashboard } from "../../components/shared/Dashboard";
import { DashboardToolbar } from "../../components/shared/DashboardToolbar";
import { FilterSidebar } from "../../loco/components/FilterSidebar";
import { INITIAL_FILTERS } from "../../constants/filters";
import { countActiveFilters } from "../../utils/filterUtils";
import TrainCaseForm from "../components/TrainCaseForm";

/** Показывает поездные случаи существующими карточками локомотивного списка */
export default function TrainDashboard() {
  const { user } = useAuth();
  const [isExporting, setIsExporting] = useState(false);
  const [filters, setFilters] = useState(INITIAL_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const filterOptions = useQuery({
    queryKey: ["train-filter-options"],
    queryFn: async () => (await api.get("/train/filter-options")).data,
  });
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [sortOrder, setSortOrder] = useState("desc");
  const [selected, setSelected] = useState(null);
  const refs = useQuery({
    queryKey: ["train-references"],
    queryFn: async () => (await api.get("/train/references")).data,
  });
  const list = useCasesList(
    { ...filters, search },
    sortOrder,
    page,
    25,
    "train",
  );
  const canCreate =
    user?.role === "superadmin" ||
    (user?.direction === "train" && user?.role === "editor");
  const totalPages = Math.max(1, Math.ceil((list.data?.total || 0) / 25));
  // Представление для общих карточек не меняет исходные данные поездного случая
  const cards = useMemo(() => {
    const equipment = new Map(
      (refs.data?.equipment || []).map((e) => [e.id, e]),
    );
    const models = new Map(
      (refs.data?.train_models || []).map((m) => [m.id, m.name]),
    );
    const name = (id) => equipment.get(id)?.name?.replaceAll("_", " ");
    return (list.data?.items || []).map((item) => ({
      ...item,
      card_view: {
        model: models.get(item.train.train_model_id),
        equipment: trainEquipmentName(item.train, equipment),
        element: name(item.train.element_id),
      },
    }));
  }, [list.data, refs.data]);
  return (
    <Dashboard
      cases={cards}
      loading={list.isPending}
      error={list.error || refs.error}
      onRetry={() => {
        list.refetch();
        refs.refetch();
      }}
      onCaseClick={(item) =>
        setSelected(list.data.items.find((c) => c.id === item.id))
      }
      currentPage={page}
      totalPages={totalPages}
      onPageChange={setPage}
      toolbar={
        <DashboardToolbar
          direction="train"
          onOpenFilters={() => setFiltersOpen(true)}
          activeCount={countActiveFilters(filters)}
          handleClearAllFilters={() => {
            setFilters(INITIAL_FILTERS);
            setPage(1);
          }}
          isExporting={isExporting}
          handleExport={async () => {
            setIsExporting(true);
            try {
              const { exportCasesToExcel } = await import("../../api/export");
              await exportCasesToExcel(
                { ...filters, search },
                "train",
                sortOrder,
              );
            } catch {
              /* Ошибку показывает общий сервис экспорта */
            } finally {
              setIsExporting(false);
            }
          }}
          sortOrder={sortOrder}
          onSort={() => {
            setSortOrder((v) => (v === "desc" ? "asc" : "desc"));
            setPage(1);
          }}
          quickCaseNumber={search ? Number(search) : null}
          onCaseNumberChange={(number) => {
            setSearch(number ? String(number) : "");
            setPage(1);
          }}
          totalCount={list.data?.total || 0}
          isSuperadmin={user?.role === "superadmin"}
          canCreate={canCreate}
          createDisabled={!refs.data}
          onCreate={() => setSelected({})}
        />
      }
    >
      <FilterSidebar
        direction="train"
        isOpen={filtersOpen}
        onClose={() => setFiltersOpen(false)}
        appliedFilters={filters}
        onApply={(value) => {
          setFilters(value);
          setPage(1);
        }}
        options={filterOptions.data}
        optionsLoading={filterOptions.isPending}
        optionsError={!!filterOptions.error}
        onRetryOptions={filterOptions.refetch}
      />
      {selected && refs.data && (
        <TrainCaseForm
          initial={selected}
          references={refs.data}
          onClose={() => setSelected(null)}
          onSaved={async (c) => {
            setSelected(c);
            await list.refetch();
          }}
        />
      )}
    </Dashboard>
  );
}
