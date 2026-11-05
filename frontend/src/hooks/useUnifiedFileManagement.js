import { useState, useEffect, useCallback, useRef } from "react";
import { useMutation, useQuery, useQueryClient, useIsMutating } from "@tanstack/react-query";

import { fileApi } from "../api/files";

export const useUnifiedFileManagement = (caseId, options = {}) => {
  const {
    category = "primary",
    relatedField = null,
    useReactQuery = true,
    pendingFiles = [],
    onFilesUploaded,
  } = options;

  const queryClient = useQueryClient();
  const [fileErrors, setFileErrors] = useState([]);

  const allFilesQueryKey = ["files", caseId];

  const {
    data: allFiles = [],
    isLoading: loading,
    error,
    refetch,
  } = useQuery({
    queryKey: allFilesQueryKey,
    queryFn: () => fileApi.getFiles(caseId),
    enabled: !!caseId && useReactQuery,
  });

  const filterFiles = (files) => files.filter((file) =>
    file.category === category && (!relatedField || file.related_field === relatedField),
  );

  // Fallback для обычного state management (если useReactQuery = false)
  const [fallbackFiles, setFallbackFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Получение файлов обычным способом (fallback)
  const fetchFiles = useCallback(async () => {
    if (!caseId || useReactQuery) return;

    try {
      const response = await fileApi.getFiles(caseId);
      setFallbackFiles(response);
    } catch (error) {
      console.error("Ошибка при загрузке файлов:", error);
    }
  }, [caseId, useReactQuery]);

  useEffect(() => {
    if (!useReactQuery) {
      fetchFiles();
    }
  }, [fetchFiles, useReactQuery]);

  // Валидация файлов
  const validateFiles = (fileList, currentFiles = caseId
    ? (useReactQuery ? allFiles : fallbackFiles)
    : pendingFiles) => {
    const errors = [];
    const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15 MB

    // Разрешенные расширения
    const allowedExtensions = {
      primary: [
        "jpg",
        "jpeg",
        "jfif",
        "png",
        "pdf",
        "doc",
        "docx",
        "txt",
        "csv",
        "rtf",
        "mp4",
        "mpeg",
        "avi",
        "mov",
        "wmv",
        "webm",
        "3gpp",
        "zip",
        "rar",
        "7z",
        "msg",
        "eml",
        "webp",
        "rpm",
      ],
      warranty: ["pdf", "jpg", "jpeg", "png", "msg", "eml"],
    };

    const currentAllowedExtensions =
      allowedExtensions[category] || allowedExtensions.primary;

    const currentTotalSize = currentFiles.reduce(
      (acc, f) => acc + (f.size_bytes ?? f.size ?? 0),
      0,
    );
    let newFilesSize = 0;

    Array.from(fileList).forEach((file) => {
      if (file.size === 0) errors.push(`Файл "${file.name}" пустой`);
      if (file.size > MAX_FILE_SIZE) {
        errors.push(`"${file.name}" слишком велик (макс. 15 МБ)`);
      }
      const ext = file.name.split(".").pop().toLowerCase();
      if (!currentAllowedExtensions.includes(ext)) {
        errors.push(`Формат .${ext} не поддерживается`);
      }
      newFilesSize += file.size;
    });

    if (currentTotalSize + newFilesSize > 50 * 1024 * 1024) {
      errors.push("Превышен общий лимит файлов для случая (50 МБ)");
    }

    return errors;
  };

  // Загрузка файлов через React Query
  const uploadMutation = useMutation({
    mutationKey: ["case-file-upload", caseId],
    mutationFn: async (fileList) => {
      const currentFiles = await queryClient.fetchQuery({
        queryKey: allFilesQueryKey,
        queryFn: () => fileApi.getFiles(caseId),
        staleTime: 0,
      });
      const errors = validateFiles(fileList, currentFiles);
      if (errors.length > 0) {
        const err = new Error("FILE_VALIDATION_ERROR");
        err.validationErrors = errors;
        throw err;
      }
      if (category === "warranty" && relatedField) {
        return fileApi.uploadWarrantyFiles(caseId, relatedField, fileList);
      } else {
        return fileApi.uploadFile(caseId, category, fileList, relatedField);
      }
    },
    onSuccess: (uploadedFiles) => {
      onFilesUploaded?.(uploadedFiles);
      setFileErrors([]);
      queryClient.invalidateQueries({ queryKey: allFilesQueryKey });
    },
    onError: (error) => {
      const validationErrors = error?.validationErrors;
      if (Array.isArray(validationErrors) && validationErrors.length > 0) {
        setFileErrors(validationErrors);
        return;
      }

      const serverErrorRaw =
        error?.response?.data?.detail ||
        error?.message ||
        "Ошибка сервера при загрузке";

      const serverError = Array.isArray(serverErrorRaw)
        ? serverErrorRaw.map((e) => {
            const msg = typeof e === "string" ? e : e?.msg;
            if (msg?.includes("Неподдерживаемый формат файла")) {
              return "Неподдерживаемый формат файла";
            }
            if (msg?.includes("Размер файла превышает")) {
              return "Размер файла превышает допустимый лимит (15 МБ)";
            }
            if (msg?.includes("Файл не должен быть пустым")) {
              return "Файл не должен быть пустым";
            }
            if (msg?.includes("Expected UploadFile")) {
              return "Ошибка загрузки: неверный формат данных";
            }
            return msg || JSON.stringify(e);
          })
        : [serverErrorRaw];

      const processedErrors = serverError.map((error) => {
        if (
          typeof error === "string" &&
          error.includes("Неподдерживаемый формат файла для категории")
        ) {
          return "Неподдерживаемый формат файла";
        }
        return error;
      });

      setFileErrors(processedErrors);
    },
  });

  // Загрузка файлов обычным способом (fallback)
  const uploadFilesFallback = async (fileList) => {
    setUploading(true);
    try {
      const currentFiles = caseId ? await fileApi.getFiles(caseId) : pendingFiles;
      const errors = validateFiles(fileList, currentFiles);
      if (errors.length > 0) {
        setFileErrors(errors);
        return false;
      }
      const response = await fileApi.uploadFile(
        caseId,
        category,
        fileList,
        relatedField,
      );
      await fetchFiles();
      setFileErrors([]);
      onFilesUploaded?.(response);
      return response;
    } catch (error) {
      const serverErrorRaw =
        error.response?.data?.detail || "Ошибка сервера при загрузке";

      let serverError = Array.isArray(serverErrorRaw)
        ? serverErrorRaw.map((e) => {
            const msg = typeof e === "string" ? e : e?.msg;
            if (msg?.includes("Неподдерживаемый формат файла для категории")) {
              return "Неподдерживаемый формат файла";
            }
            return msg || JSON.stringify(e);
          })
        : [serverErrorRaw];

      // Дополнительная обработка для ТТН и других категорий
      const processedErrors = serverError.map((error) => {
        if (
          typeof error === "string" &&
          error.includes("Неподдерживаемый формат файла для категории")
        ) {
          return "Неподдерживаемый формат файла";
        }
        return error;
      });

      setFileErrors(processedErrors);
      return false;
    } finally {
      setUploading(false);
    }
  };

  // Удаление файлов через React Query
  const deleteMutation = useMutation({
    mutationFn: (fileId) => fileApi.deleteFile(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: allFilesQueryKey });
    },
    onError: (error) => {
      console.error("Ошибка удаления файла:", error);
    },
  });

  // Привязка существующего файла к случаю
  const linkMutation = useMutation({
    mutationFn: ({ existingFileId }) =>
      fileApi.linkExistingFile(caseId, existingFileId, category, relatedField),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: allFilesQueryKey });
    },
    onError: (error) => {
      console.error("Ошибка при привязке файла:", error);
      const errorMsg = error.response?.data?.detail || "Ошибка привязки файла";
      setFileErrors((prev) => [...prev, errorMsg]);
    },
  });

  // Удаление файлов обычным способом (fallback)
  const deleteFileFallback = async (fileId) => {
    try {
      setDeleting(true);
      await fileApi.deleteFile(fileId);
      setFallbackFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch (error) {
      console.error("Ошибка при удалении:", error);
    } finally {
      setDeleting(false);
    }
  };

  // Общие функции
  const uploadFiles = useReactQuery
    ? (fileList) => uploadMutation.mutate(fileList)
    : uploadFilesFallback;

  const uploadFilesAsync = useReactQuery
    ? (fileList) => uploadMutation.mutateAsync(fileList)
    : uploadFilesFallback;

  const deleteFile = useReactQuery
    ? (fileId) => deleteMutation.mutate(fileId)
    : deleteFileFallback;

  const deleteFileAsync = useReactQuery
    ? (fileId) => deleteMutation.mutateAsync(fileId)
    : deleteFileFallback;

  const downloadFile = (fileId, fileName) => {
    fileApi.downloadFile(fileId, fileName);
  };

  const downloadArchive = () => {
    if (category === "warranty" && relatedField) {
      fileApi.downloadWarrantyArchive(caseId, relatedField);
    } else {
      fileApi.downloadArchive(caseId, category);
    }
  };

  return {
    files: filterFiles(useReactQuery ? allFiles : fallbackFiles),
    loading: useReactQuery ? loading : false,
    uploading: useReactQuery ? uploadMutation.isPending : uploading,
    isDeleting: useReactQuery ? deleteMutation.isPending : deleting,
    linkFileAsync: useReactQuery
      ? (id) => linkMutation.mutateAsync({ existingFileId: id })
      : null,
    isLinking: useReactQuery ? linkMutation.isPending : false,
    error,
    fileErrors,
    setFileErrors,
    validateFiles,
    uploadFiles,
    uploadFilesAsync,
    deleteFile,
    deleteFileAsync,
    downloadFile,
    downloadArchive,
    refetch: useReactQuery ? refetch : fetchFiles,
  };
};

/** Отслеживает только новые загрузки и подтверждает их удаление при отмене редактирования */
export function useEditFileUploads({ caseId, editing, disabled = false, onCancel, onClose, onError }) {
  const queryClient = useQueryClient();
  const uploadedIds = useRef(new Set());
  const cancelling = useRef(false);
  const [action, setAction] = useState(null);
  const [rollingBack, setRollingBack] = useState(false);
  const uploading = useIsMutating({ mutationKey: ["case-file-upload", caseId] }) > 0;

  useEffect(() => {
    if (!editing) uploadedIds.current.clear();
  }, [editing]);

  const recordUploads = (files) => {
    if (!caseId || !editing) return;
    for (const file of Array.isArray(files) ? files : []) {
      if (file?.id) uploadedIds.current.add(file.id);
    }
  };

  const requestExit = async (nextAction) => {
    if (disabled || cancelling.current) return;
    if (queryClient.isMutating({ mutationKey: ["case-file-upload", caseId] })) {
      onError("Дождитесь завершения загрузки файлов");
      return;
    }
    if (editing && uploadedIds.current.size) {
      setAction(nextAction);
      return;
    }
    await (nextAction === "close" ? onClose() : onCancel());
  };

  const confirmExit = async () => {
    if (!action || disabled || cancelling.current) return;
    if (queryClient.isMutating({ mutationKey: ["case-file-upload", caseId] })) {
      onError("Дождитесь завершения загрузки файлов");
      return;
    }
    cancelling.current = true;
    setRollingBack(true);
    try {
      const ids = [...uploadedIds.current];
      const results = await Promise.allSettled(ids.map((id) => fileApi.deleteFile(id)));
      results.forEach((result, index) => {
        if (result.status === "fulfilled" || result.reason?.response?.status === 404) {
          uploadedIds.current.delete(ids[index]);
        }
      });
      await queryClient.invalidateQueries({ queryKey: ["files", caseId] });
      if (uploadedIds.current.size) {
        setAction(null);
        onError("Не удалось удалить часть загруженных файлов. Редактирование не отменено. Повторите отмену.");
        return;
      }
      const completedAction = action;
      setAction(null);
      await (completedAction === "close" ? onClose() : onCancel());
    } catch {
      setAction(null);
      onError("Не удалось завершить отмену. Редактирование не закрыто.");
    } finally {
      cancelling.current = false;
      setRollingBack(false);
    }
  };

  return {
    recordUploads,
    busy: uploading || rollingBack,
    requestCancel: () => requestExit("cancel"),
    requestClose: () => requestExit("close"),
    confirmation: {
      show: !!action,
      fileName: null,
      title: "Выйти из режима редактирования?",
      message: "Файлы, загруженные в текущем режиме редактирования, будут удалены. Продолжить?",
      confirmLabel: "Да, выйти",
      cancelLabel: "Продолжить редактирование",
      busyLabel: "Удаление файлов...",
      isDeleting: rollingBack,
      onCancel: () => { if (!cancelling.current) setAction(null); },
      onConfirm: confirmExit,
    },
  };
}
