import React, { useEffect, useRef, useState } from "react";
import {
  FileText,
  File,
  Plus,
  Archive,
  X,
  UploadCloud,
  Download,
} from "lucide-react";

import { useUnifiedFileManagement } from "../../hooks/useUnifiedFileManagement";
import { BLOCK_TITLES } from "../../constants/labels";
import { DeleteConfirmDialog } from "../common/DeleteConfirmDialog";
import { FileValidationToast } from "../Toast/FileValidationToast";
import { getFileIcon } from "../../utils/fileUtils.jsx";

export const CaseDocuments = ({
  caseId = null,
  isEditing,
  pendingFiles = [],
  onAddFiles,
  onRemoveFile,
  onFilesUploaded,
}) => {
  const fileApi = useUnifiedFileManagement(caseId, {
    category: "primary",
    useReactQuery: true,
  });
  const [showFileToast, setShowFileToast] = useState(false);
  const fileInputRef = useRef(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);

  const isCreationMode = !caseId;
  const displayFiles = isCreationMode ? pendingFiles : fileApi.files;
  const refetchFiles = fileApi.refetch;

  const requestDeleteFile = (file) => {
    setFileToDelete(file);
    setShowDeleteConfirm(true);
  };

  const confirmDeleteFile = async () => {
    if (!fileToDelete) return;

    if (isCreationMode) {
      onRemoveFile(displayFiles.indexOf(fileToDelete));
      setShowDeleteConfirm(false);
      setFileToDelete(null);
      return;
    }

    if (!fileToDelete?.id) return;
    await fileApi.deleteFile(fileToDelete.id);
    setShowDeleteConfirm(false);
    setFileToDelete(null);
  };

  const processFiles = async (fileList) => {
    if (fileList.length === 0) return;

    if (isCreationMode) {
      onAddFiles(fileList);
      return;
    }

    const uploaded = await fileApi.uploadFiles(fileList);
    if (uploaded && onFilesUploaded) {
      onFilesUploaded(uploaded);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setIsDragActive(true);
    else if (e.type === "dragleave") setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files?.length > 0) processFiles(Array.from(e.dataTransfer.files));
  };

  const showFooter = isEditing || (!isCreationMode && displayFiles.length > 1);

  useEffect(() => {
    setShowFileToast(fileApi.fileErrors?.length > 0);
  }, [fileApi.fileErrors]);

  useEffect(() => {
    if (!isCreationMode && !isEditing) {
      refetchFiles();
    }
  }, [isCreationMode, isEditing, refetchFiles]);

  return (
    <div className="space-y-1">
      <div className="relative mb-3 flex items-center justify-between gap-2 rounded-lg border border-slate-300 bg-gradient-to-r from-slate-100 to-white px-3 py-2 shadow-md">
        <div className="absolute top-0 bottom-0 left-0 w-1 rounded-l-lg bg-slate-600"></div>
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-slate-600" />
          <h3 className="text-xs font-bold tracking-wider antialiased text-slate-700 uppercase">
            {BLOCK_TITLES.primary_docs}
          </h3>
          {displayFiles.length > 0 && (
            <span className="ml-1 rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-bold text-slate-600">
              {displayFiles.length}
            </span>
          )}
        </div>
      </div>

      <div
        onDragEnter={isEditing ? handleDrag : undefined}
        onDragLeave={isEditing ? handleDrag : undefined}
        onDragOver={isEditing ? handleDrag : undefined}
        onDrop={isEditing ? handleDrop : undefined}
        className={`relative rounded-2xl border p-2 shadow-sm transition-all duration-200 ${
          isDragActive
            ? "scale-[1.01] border-dashed border-indigo-500 bg-indigo-50"
            : "border-slate-200 bg-slate-200/50"
        }`}
      >
        <input
          type="file"
          multiple
          className="hidden"
          ref={fileInputRef}
          onChange={(e) => {
            processFiles(Array.from(e.target.files));
            e.target.value = "";
          }}
        />

        {isDragActive ? (
          <div className="flex animate-pulse flex-col items-center justify-center py-10 text-indigo-600">
            <UploadCloud className="mb-2 h-12 w-12" />
            <p className="text-sm font-bold tracking-tight uppercase">
              Отпустите для загрузки
            </p>
          </div>
        ) : (
          <>
            {displayFiles.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-4">
                <div className="mb-2 rounded-full bg-white p-4 shadow-sm">
                  <File className="h-8 w-8 text-slate-300" />
                </div>
                <p className="mb-2 text-xs font-medium tracking-tighter text-slate-500 uppercase">
                  Нет прикрепленных файлов
                </p>
                {isEditing && (
                  <button
                    onClick={() => fileInputRef.current.click()}
                    className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-bold text-slate-700 shadow-sm transition-all hover:border-indigo-300 hover:bg-slate-50 active:scale-95"
                  >
                    <Plus className="h-4 w-4 text-indigo-600" /> Выбрать файлы
                  </button>
                )}
              </div>
            ) : (
              <div className="flex flex-col gap-1.5">
                {displayFiles.map((file, idx) => (
                  <div
                    key={idx}
                    className="group flex items-center justify-between rounded-lg border border-slate-200 bg-white px-2 py-1 shadow-sm transition-all hover:border-indigo-100"
                  >
                    <div className="flex min-w-0 items-center gap-2.5">
                      {getFileIcon(file.mime_type || file.type)}
                      <div className="flex items-baseline gap-2 truncate">
                        <button
                          onClick={() =>
                            !isCreationMode &&
                            fileApi.downloadFile(file.id, file.original_name)
                          }
                          disabled={isCreationMode}
                          className={`truncate text-[12px] font-bold ${
                            isCreationMode
                              ? "cursor-default text-gray-900"
                              : "text-left text-gray-900 hover:text-indigo-600 hover:underline"
                          }`}
                        >
                          {file.original_name || file.name}
                        </button>
                        <span className="text-[11px] text-slate-400">
                          {(
                            (file.size_bytes || file.size) /
                            1024 /
                            1024
                          ).toFixed(2)}{" "}
                          MB
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {!isCreationMode && (
                        <button
                          onClick={() =>
                            fileApi.downloadFile(file.id, file.original_name)
                          }
                          className="p-1 text-slate-400 transition-colors hover:text-indigo-600"
                          title="Скачать файл"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                      )}

                      {/* Кнопка удаления */}
                      {isEditing && (
                        <button
                          onClick={() => requestDeleteFile(file)}
                          className="rounded p-1 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
                          title="Удалить"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}

                {showFooter && (
                  <div className="mt-1 flex items-center justify-between px-1">
                    {isEditing ? (
                      <button
                        onClick={() => fileInputRef.current.click()}
                        className="flex items-center gap-1.5 text-[10px] font-bold tracking-wider antialiased text-indigo-600 uppercase transition-colors hover:text-indigo-800"
                      >
                        <Plus className="h-3.5 w-3.5" /> Добавить еще
                      </button>
                    ) : (
                      <div />
                    )}

                    {!isCreationMode && displayFiles.length > 1 && (
                      <button
                        onClick={fileApi.downloadArchive}
                        className="flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-2 py-1 text-[11px] font-bold text-slate-600 shadow-sm transition-all hover:border-indigo-300 hover:text-indigo-600 active:scale-95"
                      >
                        <Archive className="h-3.5 w-3.5" /> СКАЧАТЬ ВСЕ ФАЙЛЫ
                        (ZIP)
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
      <FileValidationToast
        show={showFileToast}
        onClose={() => {
          setShowFileToast(false);
          fileApi.setFileErrors([]);
        }}
        errors={fileApi.fileErrors || []}
      />

      <DeleteConfirmDialog
        show={showDeleteConfirm}
        fileName={fileToDelete?.original_name || fileToDelete?.name}
        isDeleting={fileApi.isDeleting}
        onCancel={() => {
          setShowDeleteConfirm(false);
          setFileToDelete(null);
        }}
        onConfirm={confirmDeleteFile}
      />
    </div>
  );
};
