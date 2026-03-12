import React, { useRef, useState, useEffect } from "react";
import { Plus, X, UploadCloud, Download } from "lucide-react";
import { useUnifiedFileManagement } from "../../hooks/useUnifiedFileManagement";
import { getFileIcon } from "../../utils/fileUtils.jsx";
import { DeleteConfirmDialog } from "../common/DeleteConfirmDialog";
import { FileValidationToast } from "../Toast/FileValidationToast";

export const CompactWarrantyFiles = ({
  caseId,
  isEditing,
  relatedField,
  onFilesUploaded,
}) => {
  const fileApi = useUnifiedFileManagement(caseId, {
    category: "warranty",
    relatedField,
    useReactQuery: true,
  });

  const displayFiles = fileApi.files || [];
  const fileInputRef = useRef(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  const [showFileToast, setShowFileToast] = useState(false);

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

  const handleFilesSelected = async (fileList) => {
    if (!fileList || fileList.length === 0) return;
    const filesArray = Array.from(fileList);

    const uploaded = await fileApi.uploadFilesAsync(filesArray);
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
    if (e.dataTransfer.files?.length > 0) {
      handleFilesSelected(e.dataTransfer.files);
    }
  };

  // Режим просмотра
  if (!isEditing) {
    if (displayFiles.length === 0) {
      return (
        <div className="flex h-[38px] items-center justify-center overflow-hidden rounded-lg border border-gray-200 bg-gray-50 px-3">
          <span className="text-sm text-gray-400">Нет файлов</span>
        </div>
      );
    }

    return (
      <div className="overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-4 shadow-sm">
        <div className="flex flex-col gap-1 py-1">
          {displayFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center justify-between gap-2 overflow-hidden"
              title={file.original_name}
            >
              <div className="flex max-w-fit items-center gap-2">
                {getFileIcon(file.mime_type, file.original_name)}
                <div className="flex items-center gap-2 truncate">
                  <button
                    onClick={() =>
                      fileApi.downloadFile(file.id, file.original_name)
                    }
                    className="truncate text-left text-[12px] font-bold text-gray-900 hover:text-indigo-600 hover:underline"
                  >
                    {file.original_name}
                  </button>
                  <span className="shrink-0 text-[11px] text-slate-400">
                    {((file.size_bytes || 0) / 1024 / 1024 || 0).toFixed(2)} MB
                  </span>
                </div>
              </div>

              {/* Кнопка скачивания файла */}
              <button
                onClick={() =>
                  fileApi.downloadFile(file.id, file.original_name)
                }
                className="p-1 text-gray-400 transition-colors hover:text-indigo-600"
                title="Скачать файл"
              >
                <Download className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Режим редактирования
  if (fileApi.loading || fileApi.uploading) {
    return (
      <div className="flex h-[38px] items-center overflow-hidden rounded-lg border border-gray-300 bg-gray-50 px-3">
        <span className="text-sm text-gray-400">
          {fileApi.uploading ? "Загрузка..." : "Загрузка..."}
        </span>
      </div>
    );
  }

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      className={`relative overflow-hidden rounded-lg border transition-all duration-200 ${
        isDragActive
          ? "border-dashed border-orange-400 bg-orange-50"
          : displayFiles.length > 0
            ? "border-gray-300 bg-gray-50 shadow-sm"
            : "h-[36px] border-gray-300 bg-white"
      } ${displayFiles.length > 0 ? "" : "h-[36px]"}`}
    >
      <input
        type="file"
        multiple
        className="hidden"
        id={`file-input-${relatedField}`}
        ref={fileInputRef}
        onChange={(e) => {
          handleFilesSelected(e.target.files);
          e.target.value = "";
        }}
      />

      {isDragActive ? (
        <div className="flex h-full animate-pulse items-center justify-center text-orange-600">
          <UploadCloud className="h-4 w-4" />
        </div>
      ) : displayFiles.length === 0 ? (
        <button
          onClick={() => fileInputRef.current.click()}
          className="flex h-full w-full min-w-[200px] items-center justify-center gap-2 px-4 text-sm text-gray-400 hover:text-orange-600"
        >
          <Plus className="h-4 w-4" />
          <span>Файлы</span>
        </button>
      ) : (
        <div className="flex flex-col gap-1 px-1 py-1 pl-3">
          {displayFiles.map((file) => (
            <div key={file.id} className="flex items-center justify-between">
              <div className="group flex max-w-fit min-w-0 items-center gap-1">
                {getFileIcon(file.mime_type, file.original_name)}
                <div className="flex min-w-0 flex-1 items-baseline gap-2 truncate">
                  <button
                    onClick={() =>
                      fileApi.downloadFile(file.id, file.original_name)
                    }
                    className="min-w-0 truncate text-left text-[12px] font-bold text-gray-700 hover:text-orange-600 hover:underline"
                    title={file.original_name}
                  >
                    {file.original_name}
                  </button>
                  <span className="shrink-0 text-[11px] text-slate-400">
                    {((file.size_bytes || 0) / 1024 / 1024 || 0).toFixed(2)} MB
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-1">
                {/* Кнопка скачивания файла */}
                <button
                  onClick={() =>
                    fileApi.downloadFile(file.id, file.original_name)
                  }
                  className="p-1 text-gray-400 transition-colors hover:text-indigo-600"
                  title="Скачать файл"
                >
                  <Download className="h-4 w-4" />
                </button>

                {/* Кнопка удаления файла */}
                {isEditing && (
                  <button
                    onClick={() => requestDeleteFile(file)}
                    className="p-1 text-gray-400 transition-opacity hover:text-red-600"
                    title="Удалить файл"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}

          {isEditing && (
            <div className="px-1 pl-3">
              <button
                onClick={() => fileInputRef.current.click()}
                className="flex items-center gap-1.5 text-[10px] font-bold tracking-wider text-indigo-600 uppercase transition-colors hover:text-indigo-800"
              >
                <Plus className="h-3.5 w-3.5" /> Добавить еще
              </button>
            </div>
          )}
        </div>
      )}

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
          fileApi.setFileErrors([]);
        }}
        errors={fileApi.fileErrors || []}
      />
    </div>
  );
};
