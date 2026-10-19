import { useId, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Upload, LoaderCircle } from "lucide-react";
import api from "../../api/api";
import { useAuth } from "../../context/AuthContext";
import { formatApiError } from "../../utils/formatters";

/** Показывает ссылки на сканы экземпляра и загрузку файлов без отдельного окна */
export function PassportFiles({
  passportId,
  nodeId,
  eventId,
  side = "before",
  context,
  compact = false,
  historyLoading = false,
  historyError = false,
  retryHistory,
}) {
  const { user } = useAuth();
  const inputId = useId();
  const queryClient = useQueryClient();
  const [validationError, setValidationError] = useState("");
  const base = `/product-passports/${passportId}/nodes/${nodeId}`;
  const query = useQuery({
    queryKey: ["passport-files", passportId, nodeId, "current"],
    queryFn: async ({ signal }) =>
      (await api.get(`${base}/files`, { signal })).data,
    enabled: eventId == null,
    staleTime: 30000,
  });
  const data = eventId == null ? query.data : context;
  const loading = eventId == null ? query.isLoading : historyLoading;
  const error = eventId == null ? query.isError : historyError;
  const canEdit = ["editor", "superadmin"].includes(user?.role);
  const upload = useMutation({
    mutationFn: async (files) => {
      const body = new FormData();
      body.append("instance_key", data.instance_key);
      files.forEach((file) => body.append("files", file));
      return api.post(`${base}/files`, body, {
        params: { event_id: eventId, side },
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["passport-files", passportId, nodeId],
      });
    },
    onError: async (error) => {
      if (error.response?.status === 409) {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: ["passport-files", passportId, nodeId],
          }),
          queryClient.invalidateQueries({
            queryKey: ["product-passports", passportId, nodeId, "history"],
          }),
        ]);
      }
    },
  });

  /** Проверяет размеры сканов перед отправкой на сервер */
  const selectFiles = (event) => {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    setValidationError("");
    if (!files.length) return;
    if (
      files.length > 20 ||
      files.some((file) => !file.size || file.size > 15 * 1024 * 1024)
    ) {
      setValidationError(
        "Выберите до 20 непустых файлов, каждый не больше 15 МБ",
      );
      return;
    }
    upload.mutate(files);
  };

  /** Формирует ссылку на файл с проверкой экземпляра на сервере */
  const fileUrl = (file) => {
    const url = `/api/v1${base}/files/${file.source}/${file.id}`;
    if (file.source === "local") return url;
    const params = new URLSearchParams({
      instance_key: data.instance_key,
      side,
    });
    if (eventId != null) params.set("event_id", eventId);
    return `${url}?${params}`;
  };
  const retry = eventId == null ? () => query.refetch() : retryHistory;
  const canUpload =
    canEdit && data && (!compact || (side === "before" && !data.files.length));

  return (
    <div
      className={
        compact
          ? "mt-2 space-y-1 text-xs"
          : "space-y-2 border-t border-slate-200 pt-3 text-sm"
      }
    >
      {!compact && <p className="font-bold text-slate-900">Файлы паспорта</p>}
      {loading && (
        <p role="status" className="text-slate-600">
          Загрузка файлов…
        </p>
      )}
      {error && (
        <p role="alert" className="text-red-700">
          Не удалось загрузить файлы{" "}
          <button type="button" onClick={retry} className="underline">
            Повторить
          </button>
        </p>
      )}
      {data?.omega_error && (
        <p role="alert" className="text-red-700">
          {data.omega_error}{" "}
          <button type="button" onClick={retry} className="underline">
            Повторить
          </button>
        </p>
      )}
      {!!data?.files.length && (
        <ul className="space-y-1">
          {data.files.map((file) => (
            <li key={`${file.source}-${file.id}`}>
              <a
                href={fileUrl(file)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex max-w-full items-center gap-1.5 rounded text-left font-semibold text-indigo-700 hover:text-indigo-900 hover:underline"
                title={
                  file.source === "omega"
                    ? "Заводской файл из Omega"
                    : `Загрузил: ${file.uploaded_by || "—"}`
                }
              >
                <FileText className="h-4 w-4 shrink-0" />
                <span className="min-w-0 break-all">{file.name}</span>
              </a>
            </li>
          ))}
        </ul>
      )}
      {!compact && data && !data.files.length && !data.omega_error && (
        <p className="text-slate-600">Сканы не прикреплены</p>
      )}
      {canUpload && (
        <div>
          <input
            id={inputId}
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png,.msg"
            className="sr-only"
            onChange={selectFiles}
            disabled={upload.isPending}
          />
          <label
            htmlFor={inputId}
            className={`inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-2 py-1.5 font-bold text-indigo-700 ${upload.isPending ? "cursor-wait opacity-60" : "cursor-pointer hover:bg-indigo-100"}`}
          >
            {upload.isPending ? (
              <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Upload className="h-3.5 w-3.5" />
            )}
            {upload.isPending ? "Загрузка…" : "Добавить скан паспорта"}
          </label>
        </div>
      )}
      {(validationError || upload.isError) && (
        <p role="alert" className="text-red-700">
          {validationError ||
            formatApiError(upload.error, "Не удалось загрузить скан")}
        </p>
      )}
    </div>
  );
}
