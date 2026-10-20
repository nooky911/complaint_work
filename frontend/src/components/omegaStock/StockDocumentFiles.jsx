import { FileText } from "lucide-react";
import { omegaStockFileUrl } from "../../api/omegaStock";
import { useOmegaStockFiles } from "../../hooks/api/useOmegaStockApi";

/** Показывает вложения склада без предварительного скачивания на сервер приложения */
export function StockDocumentFiles({ kind, documentId }) {
  const {
    data: files = [],
    isPending,
    isError,
    refetch,
  } = useOmegaStockFiles(kind, documentId);
  if (isPending)
    return <p className="text-sm text-slate-600">Загрузка файлов...</p>;
  if (isError)
    return (
      <p role="alert" className="text-sm text-red-700">
        Не удалось загрузить файлы{" "}
        <button type="button" onClick={() => refetch()} className="underline">
          Повторить
        </button>
      </p>
    );
  return (
    <div className="flex flex-wrap items-center gap-4 text-sm">
      {files.length === 0 && (
        <span className="text-slate-600">У документа нет вложений</span>
      )}
      {files.map((file) => (
        <a
          key={file.id}
          href={omegaStockFileUrl(kind, documentId, file.id)}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 font-semibold text-indigo-700 hover:underline"
        >
          <FileText className="h-4 w-4 shrink-0" />
          {file.name}
        </a>
      ))}
    </div>
  );
}
