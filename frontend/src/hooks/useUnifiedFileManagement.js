import { useState, useEffect, useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fileApi } from "../api/files";

export const useUnifiedFileManagement = (caseId, options = {}) => {
  const {
    category = "primary",
    relatedField = null,
    useReactQuery = true,
  } = options;

  const queryClient = useQueryClient();
  const [fileErrors, setFileErrors] = useState([]);

  const groupedFilesQueryKey = ["filesGrouped", caseId];

  const listFilesQueryKey = ["files", caseId, category];
  const allFilesQueryKey = ["files", caseId];

  const {
    data: groupedFiles,
    isLoading: groupedLoading,
    error: groupedError,
    refetch: refetchGrouped,
  } = useQuery({
    queryKey: groupedFilesQueryKey,
    queryFn: () => fileApi.getFilesGrouped(caseId),
    enabled: !!caseId && !!relatedField && useReactQuery,
  });

  const {
    data: files = [],
    isLoading: loading,
    error,
    refetch,
  } = useQuery({
    queryKey: listFilesQueryKey,
    queryFn: async () => {
      const all = await fileApi.getFiles(caseId);
      return category === "warranty"
        ? all.filter((file) => file.category === "warranty")
        : all.filter((file) => file.category === category);
    },
    enabled: !!caseId && !relatedField && useReactQuery,
    ...(!useReactQuery && { enabled: false }),
  });

  const effectiveFiles = relatedField
    ? groupedFiles?.[relatedField] || []
    : files;

  const effectiveLoading = relatedField ? groupedLoading : loading;
  const effectiveError = relatedField ? groupedError : error;
  const effectiveRefetch = relatedField ? refetchGrouped : refetch;

  // Fallback для обычного state management (если useReactQuery = false)
  const [fallbackFiles, setFallbackFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Получение файлов обычным способом (fallback)
  const fetchFiles = useCallback(async () => {
    if (!caseId || useReactQuery) return;

    try {
      const response = relatedField
        ? await fileApi.getWarrantyFiles(caseId, relatedField)
        : await fileApi.getFiles(caseId);

      const filteredFiles =
        category === "warranty"
          ? response.filter((file) => file.category === "warranty")
          : response.filter((file) => file.category === category);

      setFallbackFiles(filteredFiles);
    } catch (error) {
      console.error("Ошибка при загрузке файлов:", error);
    }
  }, [caseId, category, relatedField, useReactQuery]);

  useEffect(() => {
    if (!useReactQuery) {
      fetchFiles();
    }
  }, [fetchFiles, useReactQuery]);

  // Валидация файлов
  const validateFiles = (fileList) => {
    const errors = [];
    const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15 MB

    // Разрешенные расширения
    const allowedExtensions = {
      primary: [
        "jpg",
        "jpeg",
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
      ],
      warranty: ["pdf", "jpg", "jpeg", "png", "msg"],
    };

    const currentAllowedExtensions =
      allowedExtensions[category] || allowedExtensions.primary;

    const currentFiles = useReactQuery ? files : fallbackFiles;
    const currentTotalSize = currentFiles.reduce(
      (acc, f) => acc + (f.size_bytes || 0),
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
    mutationFn: (fileList) => {
      const errors = validateFiles(fileList);
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
    onSuccess: () => {
      setFileErrors([]);
      queryClient.invalidateQueries({ queryKey: listFilesQueryKey });
      queryClient.invalidateQueries({ queryKey: allFilesQueryKey });
      queryClient.invalidateQueries({ queryKey: groupedFilesQueryKey });
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

      setFileErrors(serverError);
    },
  });

  // Загрузка файлов обычным способом (fallback)
  const uploadFilesFallback = async (fileList) => {
    const errors = validateFiles(fileList);
    if (errors.length > 0) {
      setFileErrors(errors);
      return false;
    }

    setUploading(true);
    try {
      const response = await fileApi.uploadFile(
        caseId,
        category,
        fileList,
        relatedField,
      );
      await fetchFiles();
      setFileErrors([]);
      return response.data;
    } catch (error) {
      const serverError =
        error.response?.data?.detail || "Ошибка сервера при загрузке";
      setFileErrors(Array.isArray(serverError) ? serverError : [serverError]);
      return false;
    } finally {
      setUploading(false);
    }
  };

  // Удаление файлов через React Query
  const deleteMutation = useMutation({
    mutationFn: (fileId) => fileApi.deleteFile(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listFilesQueryKey });
      queryClient.invalidateQueries({ queryKey: allFilesQueryKey });
      queryClient.invalidateQueries({ queryKey: groupedFilesQueryKey });
    },
    onError: (error) => {
      console.error("Ошибка удаления файла:", error);
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
    files: useReactQuery ? effectiveFiles : fallbackFiles,
    loading: useReactQuery ? effectiveLoading : false,
    uploading: useReactQuery ? uploadMutation.isPending : uploading,
    isDeleting: useReactQuery ? deleteMutation.isPending : deleting,
    error: effectiveError,
    fileErrors,
    setFileErrors,
    uploadFiles,
    uploadFilesAsync,
    deleteFile,
    deleteFileAsync,
    downloadFile,
    downloadArchive,
    refetch: useReactQuery ? effectiveRefetch : fetchFiles,
  };
};
