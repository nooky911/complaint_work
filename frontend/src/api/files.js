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

  // Загрузка файлов warranty
  uploadWarrantyFiles: async (caseId, relatedField, files) => {
    const filesArray = Array.isArray(files) ? files : [files];

    if (filesArray.length === 0) {
      return [];
    }

    const formData = new FormData();
    formData.append("category", "warranty");
    formData.append("related_field", relatedField);

    filesArray.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await api.post(
        `/files/cases/${caseId}/upload-files`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Загрузка одного файла
  uploadFile: async (caseId, category, fileList, relatedField = null) => {
    const filesArray = Array.isArray(fileList) ? fileList : [fileList];
    if (filesArray.length === 0) throw new Error("No files provided");

    console.log("uploadFile called with:", {
      caseId,
      category,
      filesArray: filesArray.map((f) => ({
        name: f.name,
        size: f.size,
        type: f.type,
      })),
      relatedField,
    });

    // Определяем эндпоинт в зависимости от количества файлов
    const isMultipleFiles = filesArray.length > 1;
    const endpoint = isMultipleFiles
      ? `/files/cases/${caseId}/upload-files`
      : `/files/cases/${caseId}/upload`;

    console.log(
      "Using endpoint:",
      endpoint,
      "isMultipleFiles:",
      isMultipleFiles,
    );

    const formData = new FormData();
    formData.append("category", category);
    if (relatedField) {
      formData.append("related_field", relatedField);
    }

    if (isMultipleFiles) {
      filesArray.forEach((file) => {
        formData.append("files", file);
      });
    } else {
      formData.append("file", filesArray[0]);
    }

    const response = await api.post(endpoint, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
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

        // Убрать префикс utf-8
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
};
