import React from "react";
import { FileText, Image as ImageIcon, File, Archive } from "lucide-react";

// Иконки
export const getFileIcon = (mimeType, fileName = "") => {
  const name = fileName.toLowerCase();

  // ИЗОБРАЖЕНИЯ
  if (mimeType?.includes("image") || /\.(jpg|jpeg|png|gif|webp)$/.test(name)) {
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
    /\.(zip|rar|7z)$/.test(name)
  ) {
    return <Archive className="h-3 w-3 shrink-0 text-amber-500" />;
  }

  // Дефолтный файл
  return <File className="h-3 w-3 shrink-0 text-slate-400" />;
};
