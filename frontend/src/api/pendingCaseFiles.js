import api from "./api";

/** Загружает отложенные файлы и ссылки после создания случая любого направления */
export async function uploadPendingCaseFiles(
  caseId,
  files,
  category = "primary",
) {
  const uploads = files.filter((file) => !file.isLink);
  if (uploads.length) {
    const form = new FormData();
    form.append("category", category);
    uploads.forEach((file) => form.append("files", file.file ?? file));
    await api.post(`/files/cases/${caseId}/upload-files`, form);
  }
  for (const file of files.filter((item) => item.isLink)) {
    const form = new FormData();
    form.append("existing_file_id", file.existingFileId);
    form.append("category", category);
    await api.post(`/files/cases/${caseId}/link-file`, form);
  }
}
