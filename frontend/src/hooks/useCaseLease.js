import { useEffect, useRef } from "react";
import api from "../api/api";

/** Поддерживает блокировку и освобождает её при уходе из редактирования */
export function useCaseLease({
  caseId,
  editing,
  heartbeatPath,
  unlockPath,
  saving = false,
  onError,
}) {
  const state = useRef({ saving, onError });
  useEffect(() => {
    state.current = { saving, onError };
  }, [saving, onError]);
  useEffect(() => {
    if (!caseId || !editing) return;
    let stopped = false;
    let pending = false;
    const renew = async () => {
      if (stopped || pending) return;
      pending = true;
      try {
        await api.post(heartbeatPath);
      } catch (error) {
        if (!stopped && error.response?.status === 423) clearInterval(timer);
        if (!stopped && !state.current.saving) state.current.onError?.(error);
      } finally {
        pending = false;
      }
    };
    const release = () =>
      fetch(`${api.defaults.baseURL}${unlockPath}`, {
        method: "POST",
        credentials: "include",
        keepalive: true,
      }).catch(() => {});
    const timer = setInterval(renew, 30000);
    window.addEventListener("pagehide", release);
    window.addEventListener("pageshow", renew);
    return () => {
      stopped = true;
      clearInterval(timer);
      window.removeEventListener("pagehide", release);
      window.removeEventListener("pageshow", renew);
      release();
    };
  }, [caseId, editing, heartbeatPath, unlockPath]);
}
