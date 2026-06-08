import React from "react";
import {
  FileText,
  Image as ImageIcon,
  File,
  Archive,
  Mail,
} from "lucide-react";

// Иконки
export const getFileIcon = (mimeTypeOrFile, fileName = "") => {
  const mimeType =
    typeof mimeTypeOrFile === "object"
      ? mimeTypeOrFile?.mime_type || mimeTypeOrFile?.type || ""
      : mimeTypeOrFile || "";

  const rawName =
    typeof mimeTypeOrFile === "object"
      ? mimeTypeOrFile?.original_name || mimeTypeOrFile?.name || fileName || ""
      : fileName || "";

  // Защита от null и пустых строк
  const name = (rawName || "").trim().toLowerCase();

  // ИЗОБРАЖЕНИЯ
  if (
    mimeType?.includes("image") ||
    /\.(jpg|jpeg|png|gif|webp|jfif)$/.test(name)
  ) {
    return <ImageIcon className="h-3 w-3 shrink-0 text-blue-500" />;
  }

  // PDF
  if (mimeType?.includes("pdf") || name.endsWith(".pdf")) {
    return <FileText className="h-3 w-3 shrink-0 text-red-600" />;
  }

  // WORD
  if (mimeType?.includes("word") || /\.(docx|doc)$/.test(name)) {
    return <FileText className="h-3 w-3 shrink-0 text-blue-700" />;
  }

  // EXCEL
  if (
    mimeType?.includes("sheet") ||
    mimeType?.includes("excel") ||
    /\.(xlsx|xls|csv)$/.test(name)
  ) {
    return <File className="h-3 w-3 shrink-0 text-green-700" />;
  }

  // АРХИВЫ
  if (
    mimeType?.includes("zip") ||
    mimeType?.includes("rar") ||
    /\.(zip|rar|7z|rpm)$/.test(name)
  ) {
    return <Archive className="h-3 w-3 shrink-0 text-amber-600" />;
  }

  // ПИСЬМА OUTLOOK (.msg)
  if (
    mimeType?.includes("outlook") ||
    mimeType?.includes("msg") ||
    name.endsWith(".msg")
  ) {
    return <Mail className="h-3 w-3 shrink-0 text-yellow-500" />;
  }

  // ПО УМОЛЧАНИЮ
  return <File className="h-3 w-3 shrink-0 text-slate-400" />;
};
