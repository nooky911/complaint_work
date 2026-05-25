import React, { useRef, useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Plus, X, UploadCloud, Download, Link as LinkIcon } from "lucide-react";
import { useUnifiedFileManagement } from "../../hooks/useUnifiedFileManagement";
import { getFileIcon } from "../../utils/fileUtils.jsx";
import { DeleteConfirmDialog } from "../common/DeleteConfirmDialog";
import { FileValidationToast } from "../Toast/FileValidationToast";
import { LinkFileModal } from "../common/LinkFileModal";

export const BaseCompactFiles = ({
  caseId,
  isEditing,
  relatedField,
  category,
}) => {
  const fileApi = useUnifiedFileManagement(caseId, {
    category: category,
    relatedField,
    useReactQuery: !!caseId,
  });

  const displayFiles = fileApi.files || [];
  const fileInputRef = useRef(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  const [showFileToast, setShowFileToast] = useState(false);
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [showChoiceModal, setShowChoiceModal] = useState(false);

  useEffect(() => {
    setShowFileToast(fileApi.fileErrors?.length > 0);
  }, [fileApi.fileErrors]);

  const requestDeleteFile = (file) => {
    setFileToDelete(file);
    setShowDeleteConfirm(true);
  };

  const confirmDeleteFile = () => {
    if (!fileToDelete?.id) return;
    fileApi.deleteFile(fileToDelete.id);
    setShowDeleteConfirm(false);
    setFileToDelete(null);
  };

  const handleFilesChange = (e) => {
    if (!e.target.files || e.target.files.length === 0) return;
    fileApi.uploadFiles(e.target.files);
  };

  const handleLinkFile = async (existingFileId) => {
    try {
      await fileApi.linkFileAsync(existingFileId);
    } catch (error) {
      console.error("Ошибка привязки файла:", error);
    }
  };

  const handleDragIn = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (isEditing) setIsDragActive(true);
  };

  const handleDragOut = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (!isEditing) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      fileApi.uploadFiles(e.dataTransfer.files);
    }
  };

  const handleAddClick = (e) => {
    if (e) e.stopPropagation();
    if (!isEditing) return;

    if (caseId) {
      setShowChoiceModal(true);
    } else {
      fileInputRef.current.click();
    }
  };

  if (!isEditing && displayFiles.length === 0) return null;

  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFilesChange}
        className="hidden"
        multiple
      />

      <div className="mt-2">
        {displayFiles.length === 0 ? (
          <div
            onClick={handleAddClick}
            onDragEnter={handleDragIn}
            onDragLeave={handleDragOut}
            onDragOver={handleDragIn}
            onDrop={handleDrop}
            className={`flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-dashed p-2 text-gray-500 transition-all ${
              isDragActive
                ? "scale-[0.99] border-indigo-500 bg-indigo-50 text-indigo-600"
                : "border-gray-300 bg-gray-50 hover:border-indigo-400 hover:bg-indigo-50/20"
            }`}
          >
            <UploadCloud className="h-4 w-4 text-gray-400" />
            <span className="text-xs font-medium">
              Перетащите файлы сюда или кликните
            </span>
          </div>
        ) : (
          <div className="flex flex-col gap-1.5">
            {displayFiles.map((file) => (
              <div
                key={file.id}
                className="group flex items-center justify-between rounded-lg border border-slate-200 bg-white px-2 py-1 shadow-sm transition-all hover:border-indigo-100"
              >
                <div className="flex min-w-0 items-center gap-2.5 overflow-hidden">
                  {getFileIcon(file.mime_type || file.type)}
                  <div className="flex items-baseline gap-2 truncate">
                    <button
                      onClick={() =>
                        fileApi.downloadFile(file.id, file.original_name)
                      }
                      className="truncate text-left text-[12px] font-bold text-gray-900 hover:text-indigo-600 hover:underline"
                      title={file.original_name || file.name}
                    >
                      {file.original_name || file.name}
                    </button>
                    <span className="shrink-0 text-[11px] text-slate-400">
                      {(
                        (file.size_bytes || file.size || 0) /
                        1024 /
                        1024
                      ).toFixed(2)}{" "}
                      MB
                    </span>
                  </div>
                </div>

                {/* Правая часть: Кнопки */}
                <div className="flex shrink-0 items-center gap-1">
                  <button
                    onClick={() =>
                      fileApi.downloadFile(file.id, file.original_name)
                    }
                    className="p-1 text-slate-400 transition-colors hover:text-indigo-600"
                    title="Скачать файл"
                  >
                    <Download className="h-4 w-4" />
                  </button>

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
            {isEditing && (
              <div className="mt-1 flex items-center justify-between px-1">
                <button
                  onClick={handleAddClick}
                  className="flex items-center gap-1.5 text-[10px] font-bold tracking-wider text-indigo-600 uppercase antialiased transition-colors hover:text-indigo-800"
                >
                  <Plus className="h-3.5 w-3.5" /> Добавить еще
                </button>
              </div>
            )}
          </div>
        )}
      </div>

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

      <FileValidationToast
        show={showFileToast}
        onClose={() => {
          setShowFileToast(false);
        }}
        errors={fileApi.fileErrors || []}
      />

      {/* Окно поиска по базе */}
      <LinkFileModal
        isOpen={showLinkModal}
        onClose={() => setShowLinkModal(false)}
        onSelect={handleLinkFile}
        category={category}
        relatedField={relatedField}
        currentFiles={displayFiles}
      />

      {showChoiceModal &&
        createPortal(
          <div
            className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm"
            onClick={() => setShowChoiceModal(false)}
          >
            <div
              className="animate-in zoom-in-95 w-full max-w-sm rounded-xl bg-white p-6 shadow-2xl duration-200"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm font-black tracking-wider text-slate-800 uppercase">
                  Добавление документа
                </h3>
                <button
                  onClick={() => setShowChoiceModal(false)}
                  className="rounded-full p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="flex flex-col gap-3">
                <button
                  onClick={() => {
                    setShowChoiceModal(false);
                    fileInputRef.current.click();
                  }}
                  className="flex items-center gap-3 rounded-lg border border-indigo-200 bg-indigo-50/50 p-3 text-left font-semibold text-indigo-700 transition-all hover:bg-indigo-100"
                >
                  <UploadCloud className="h-5 w-5 text-indigo-600" />
                  <div className="flex flex-col">
                    <span className="text-sm">Загрузить с компьютера</span>
                    <span className="text-[11px] font-normal text-slate-500">
                      Выбрать локальный файл
                    </span>
                  </div>
                </button>

                <button
                  onClick={() => {
                    setShowChoiceModal(false);
                    setShowLinkModal(true);
                  }}
                  className="flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50/50 p-3 text-left font-semibold text-emerald-700 transition-all hover:bg-emerald-100"
                >
                  <LinkIcon className="h-5 w-5 text-emerald-600" />
                  <div className="flex flex-col">
                    <span className="text-sm">Выбрать из загруженных</span>
                    <span className="text-[11px] font-normal text-slate-500">
                      Привязать файл из базы данных
                    </span>
                  </div>
                </button>

                <button
                  onClick={() => setShowChoiceModal(false)}
                  className="mt-2 rounded-lg border border-gray-300 bg-white py-2 text-center text-sm font-bold text-gray-700 transition-colors hover:bg-gray-50"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>,
          document.body,
        )}
    </>
  );
};
