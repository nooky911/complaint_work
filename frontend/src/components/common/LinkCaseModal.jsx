import React, { useState } from "react";
import { createPortal } from "react-dom";
import { Search, X, Copy, FileText, Train } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import api from "../../api/api";
import { fileApi } from "../../api/files";
import { useDebouncedValue } from "../../hooks/useDebounce";
import { ErrorToast } from "../Toast/ErrorToast";

export const LinkCaseModal = ({
  isOpen,
  onClose,
  onSelect,
  currentCaseId,
  currentFiles = [],
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearch = useDebouncedValue(searchTerm, 400);
  const [isProcessing, setIsProcessing] = useState(false);
  const [toastConfig, setToastConfig] = useState({
    show: false,
    title: "",
    message: "",
    type: "info",
  });

  const { data: cases = [], isLoading } = useQuery({
    queryKey: ["cases_list_for_link"],
    queryFn: async () => {
      const response = await api.get("/cases");
      return Array.isArray(response.data)
        ? response.data
        : response.data.items || [];
    },
    enabled: isOpen,
  });

  // Фильтруем случаи по номеру (display_number) или номеру локомотива
  const filteredCases = cases.filter((c) => {
    if (currentCaseId && c.id === currentCaseId) return false;

    if (!debouncedSearch) return true;
    const term = debouncedSearch.toLowerCase();

    // 2. Ищем именно по визуальному номеру, а не по ID БД
    return (
      String(c.display_number || c.id).includes(term) ||
      String(c.locomotive_number || "")
        .toLowerCase()
        .includes(term)
    );
  });

  const handleSelectCase = async (selectedCase) => {
    setIsProcessing(true);
    try {
      const allFiles = await fileApi.getFiles(selectedCase.id);
      const primaryFiles = allFiles.filter((f) => f.category === "primary");

      if (primaryFiles.length === 0) {
        setToastConfig({
          show: true,
          title: "Внимание",
          message: "В выбранном случае нет первичных документов!",
          type: "warning",
        });
        setIsProcessing(false);
        return;
      }

      let addedCount = 0;
      for (const file of primaryFiles) {
        const isAlreadyAttached = currentFiles.some(
          (cf) =>
            cf.id === file.id ||
            cf.existingFileId === file.id ||
            cf.original_name === file.original_name ||
            cf.name === file.original_name,
        );

        if (!isAlreadyAttached) {
          await onSelect(file.id, file);
          addedCount++;
        }
      }

      if (addedCount === 0) {
        setToastConfig({
          show: true,
          title: "Уже прикреплено",
          message: "Все документы из этого случая уже есть в вашем списке.",
          type: "info",
        });
        setIsProcessing(false);
      } else {
        onClose();
      }
    } catch (error) {
      console.error("Ошибка при получении файлов случая:", error);
      setToastConfig({
        show: true,
        title: "Ошибка",
        message: "Не удалось загрузить файлы случая.",
        type: "error",
      });
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;

  return createPortal(
    <>
      <ErrorToast
        show={toastConfig.show}
        onClose={() => setToastConfig((prev) => ({ ...prev, show: false }))}
        title={toastConfig.title}
        message={toastConfig.message}
        type={toastConfig.type}
      />
      <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
        <div className="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl">
          {/* Шапка */}
          <div className="flex items-center justify-between border-b border-gray-200 bg-slate-50 px-6 py-4">
            <div className="flex items-center gap-2 text-slate-800">
              <Copy className="h-5 w-5 text-indigo-600" />
              <h3 className="text-lg font-bold">
                Импорт первички из другого случая
              </h3>
            </div>
            <button
              onClick={onClose}
              disabled={isProcessing}
              className="rounded-full p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700 disabled:opacity-50"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Поиск */}
          <div className="border-b border-gray-200 p-4">
            <div className="relative">
              <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск по номеру случая или локомотива..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg border border-gray-300 py-2 pr-4 pl-9 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Список случаев */}
          <div className="custom-scrollbar flex-1 overflow-y-auto p-4">
            {isLoading ? (
              <div className="flex h-32 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent"></div>
              </div>
            ) : filteredCases.length === 0 ? (
              <div className="flex h-32 flex-col items-center justify-center text-slate-400">
                <FileText className="mb-2 h-8 w-8 opacity-50" />
                <p className="text-sm">Случаи не найдены</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredCases.map((c) => (
                  <div
                    key={c.id}
                    className="flex items-center justify-between rounded-lg border border-gray-200 p-3 transition-colors hover:border-indigo-300 hover:bg-indigo-50/30"
                  >
                    <div className="flex flex-col">
                      <span className="text-sm font-bold text-slate-700">
                        Случай #{c.display_number || c.id}
                      </span>
                      <span className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
                        <Train className="h-3 w-3" /> Локомотив:{" "}
                        {c.locomotive_number || "Не указан"}
                      </span>
                    </div>
                    <button
                      onClick={() => handleSelectCase(c)}
                      disabled={isProcessing}
                      className="ml-4 shrink-0 rounded-md bg-indigo-50 px-3 py-1.5 text-xs font-bold text-indigo-700 transition-colors hover:bg-indigo-100 disabled:opacity-50"
                    >
                      {isProcessing ? "Копирование..." : "Прикрепить файлы"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>,
    document.body,
  );
};
