import api from "./api.js";

const triggerDownload = (blobData, fileName) => {
  const url = window.URL.createObjectURL(new Blob([blobData]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", fileName);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const fileApi = {
  // Получение всех файлов случая
  getFiles: async (caseId) => {
    const response = await api.get(`/files/cases/${caseId}`);
    return response.data;
  },

  getFilesGrouped: async (caseId) => {
    const response = await api.get(`/files/cases/${caseId}/grouped`);
    return response.data;
  },

  // Получение файлов warranty для конкретного поля
  getWarrantyFiles: async (caseId, relatedField) => {
    const groupedFiles = await fileApi.getFilesGrouped(caseId);
    return groupedFiles[relatedField] || [];
  },

  uploadWarrantyFiles: async (caseId, relatedField, files) => {
    const filesArray = Array.from(files || []);

    if (filesArray.length === 0) return [];

    const formData = new FormData();
    formData.append("category", "warranty");
    formData.append("related_field", relatedField);

    filesArray.forEach((file) => formData.append("files", file));

    const response = await api.post(
      `/files/cases/${caseId}/upload-files`,
      formData,
    );
    return response.data;
  },

  uploadFile: async (caseId, category, fileList, relatedField = null) => {
    const filesArray = Array.from(fileList || []);

    if (filesArray.length === 0) throw new Error("No files provided");

    const formData = new FormData();
    formData.append("category", category);

    if (
      relatedField !== null &&
      relatedField !== undefined &&
      relatedField !== ""
    ) {
      formData.append("related_field", relatedField);
    }

    filesArray.forEach((file) => {
      formData.append("files", file);
    });

    const response = await api.post(
      `/files/cases/${caseId}/upload-files`,
      formData,
    );
    return response.data;
  },

  // Удаление файла
  deleteFile: async (fileId) => {
    await api.delete(`/files/${fileId}`);
  },

  // Скачивание файла
  downloadFile: async (fileId, fileName) => {
    const response = await api.get(`/files/${fileId}/download`, {
      responseType: "blob",
    });

    triggerDownload(response.data, fileName);
  },

  // Скачивание архива warranty файлов
  downloadWarrantyArchive: async (caseId, relatedField) => {
    const formData = new FormData();
    formData.append("category", "warranty");

    const response = await api.post(
      `/files/cases/${caseId}/archive`,
      formData,
      {
        responseType: "blob",
      },
    );

    triggerDownload(response.data, `warranty_${relatedField}_${caseId}.zip`);
  },

  // Скачивание архива всех файлов
  downloadArchive: async (caseId, category) => {
    const formData = new FormData();
    formData.append("category", category);

    const response = await api.post(
      `/files/cases/${caseId}/archive`,
      formData,
      {
        responseType: "blob",
      },
    );

    let fileName = `${category}_files_${caseId}.zip`;

    const contentDisposition = response.headers["content-disposition"];
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(
        /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/,
      );
      if (filenameMatch && filenameMatch[1]) {
        fileName = filenameMatch[1].replace(/['"]/g, "");

        if (fileName.startsWith("utf-8")) {
          fileName = fileName.substring(5);
          if (fileName.startsWith("_")) {
            fileName = fileName.substring(1);
          }
        }
      }
    }

    if (fileName.includes("%")) {
      try {
        fileName = decodeURIComponent(fileName);
      } catch (e) {}
    }

    triggerDownload(response.data, fileName);
  },

  // Поиск уникальных файлов для переиспользования
  searchUniqueFiles: async (category, relatedField = null, query = null) => {
    const params = new URLSearchParams({ category });
    if (relatedField) params.append("related_field", relatedField);
    if (query) params.append("query", query);

    const response = await api.get(`/files/search/unique?${params.toString()}`);
    return response.data;
  },

  linkExistingFile: async (
    caseId,
    existingFileId,
    category,
    relatedField = null,
  ) => {
    const formData = new FormData();
    formData.append("existing_file_id", existingFileId);
    formData.append("category", category);
    if (relatedField) formData.append("related_field", relatedField);

    const response = await api.post(
      `/files/cases/${caseId}/link-file`,
      formData,
    );
    return response.data;
  },
};
