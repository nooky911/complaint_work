import React, { useState } from "react";
import { createPortal } from "react-dom";
import { Search, X, Link as LinkIcon, FileText } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fileApi } from "../../api/files";
import { useDebouncedValue } from "../../hooks/useDebounce";
import { getFileIcon } from "../../utils/fileUtils";
import { ErrorToast } from "../Toast/ErrorToast";

export const LinkFileModal = ({
  isOpen,
  onClose,
  onSelect,
  category,
  relatedField,
  currentCaseId,
  currentFiles = [],
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const debouncedSearch = useDebouncedValue(searchTerm, 400);
  const [toastConfig, setToastConfig] = useState({
    show: false,
    title: "",
    message: "",
    type: "info",
  });

  // Поисков файлов при открытом окне
  const { data: files = [], isLoading } = useQuery({
    queryKey: ["searchFiles", category, relatedField, debouncedSearch],
    queryFn: async () => {
      if (
        category === "warranty" &&
        (relatedField === "notification" || relatedField === "re_notification")
      ) {
        const [notifFiles, reNotifFiles] = await Promise.all([
          fileApi.searchUniqueFiles(category, "notification", debouncedSearch),
          fileApi.searchUniqueFiles(
            category,
            "re_notification",
            debouncedSearch,
          ),
        ]);

        const combined = [...notifFiles, ...reNotifFiles];

        const uniqueMap = new Map();
        combined.forEach((f) => uniqueMap.set(f.id, f));
        return Array.from(uniqueMap.values());
      }

      return fileApi.searchUniqueFiles(category, relatedField, debouncedSearch);
    },
    enabled: isOpen,
    staleTime: 0,
    gcTime: 0,
  });

  const otherCasesFiles = files.filter((f) => f.case_id !== currentCaseId);

  const uniqueFilesMap = new Map();
  otherCasesFiles.forEach((file) => {
    if (!uniqueFilesMap.has(file.original_name)) {
      uniqueFilesMap.set(file.original_name, file);
    }
  });

  const filteredFiles = Array.from(uniqueFilesMap.values());

  const handleSelectFile = (file) => {
    const isAlreadyAttached = currentFiles.some(
      (cf) =>
        cf.id === file.id ||
        cf.existingFileId === file.id ||
        cf.original_name === file.original_name ||
        cf.name === file.original_name,
    );

    if (isAlreadyAttached) {
      setToastConfig({
        show: true,
        title: "Уже прикреплено",
        message: "Этот файл уже добавлен к текущему случаю.",
        type: "warning",
      });
      return;
    }

    onSelect(file.id, file);
    onClose();
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
          {/* Шапка модалки */}
          <div className="flex items-center justify-between border-b border-gray-200 bg-slate-50 px-6 py-4">
            <div className="flex items-center gap-2 text-slate-800">
              <LinkIcon className="h-5 w-5 text-indigo-600" />
              <h3 className="text-lg font-bold">
                Выбрать из ранее загруженных
              </h3>
            </div>
            <button
              onClick={onClose}
              className="rounded-full p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Строка поиска */}
          <div className="border-b border-gray-200 p-4">
            <div className="relative">
              <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск по названию файла..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg border border-gray-300 py-2 pr-4 pl-9 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Список файлов */}
          <div className="custom-scrollbar flex-1 overflow-y-auto p-4">
            {isLoading ? (
              <div className="flex h-32 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent"></div>
              </div>
            ) : filteredFiles.length === 0 ? (
              <div className="flex h-32 flex-col items-center justify-center text-slate-400">
                <FileText className="mb-2 h-8 w-8 opacity-50" />
                <p className="text-sm">Ничего не найдено</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredFiles.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between rounded-lg border border-gray-200 p-3 transition-colors hover:border-indigo-300 hover:bg-indigo-50/30"
                  >
                    <div className="flex items-center gap-3 overflow-hidden">
                      {getFileIcon(file.mime_type, file.original_name)}
                      <span className="truncate text-sm font-medium text-slate-700">
                        {file.original_name}
                      </span>
                    </div>
                    <button
                      onClick={() => handleSelectFile(file)}
                      className="ml-4 shrink-0 rounded-md bg-indigo-50 px-3 py-1.5 text-xs font-bold text-indigo-700 transition-colors hover:bg-indigo-100"
                    >
                      Выбрать
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
