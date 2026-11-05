import { useCallback, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { canAssignCaseOwner } from "../../utils/userSections";
import api from "../../api/api";
import { useAuth } from "../../context/AuthContext";
import { useCaseLease } from "../../hooks/useCaseLease";
import { uploadPendingCaseFiles } from "../../api/pendingCaseFiles";
import { blank, message, trainCasePayload } from "../utils/caseFormData";

/** Управляет поездной записью, сохранением, отменой и блокировкой */
export function useTrainCaseForm({ initial, onClose, onSaved }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [data, setData] = useState(() =>
    initial.id
      ? structuredClone(initial)
      : {
          ...blank(),
          user_id: canAssignCaseOwner(user, "train") ? user.id : null,
        },
  );
  const [editing, setEditing] = useState(!initial.id),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [pendingFiles, setPendingFiles] = useState([]);
  const [baseline, setBaseline] = useState(initial);
  const usersQuery = useQuery({
    queryKey: ["users"],
    queryFn: async () => (await api.get("/users/")).data,
    enabled: user.role === "superadmin",
  });
  const id = data.id;
  useCaseLease({
    caseId: id,
    editing,
    saving: busy,
    heartbeatPath: `/train/cases/${id}/heartbeat`,
    unlockPath: `/train/cases/${id}/unlock`,
    onError: (e) => setError(message(e)),
  });
  const update = useCallback(
    (key, value) =>
      setData((d) => {
        const next = value === "" ? null : (value ?? null);
        return d[key] === next
          ? d
          : {
              ...d,
              [key]: next,
            };
      }),
    [],
  );
  const startEdit = async () => {
    setBusy(true);
    setError("");
    try {
      const fresh = (await api.post(`/train/cases/${id}/lock`)).data;
      setData(fresh);
      setBaseline(fresh);
      setEditing(true);
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  };
  const close = () => {
    if (busy) return;
    if (id && editing) api.post(`/train/cases/${id}/unlock`).catch(() => {});
    onClose();
  };
  const save = async (passportLinks) => {
    setError("");
    setBusy(true);
    try {
      const payload = trainCasePayload(data);
      if (passportLinks) payload.passport_links = passportLinks;
      const saved = (
        await (id
          ? api.put(`/train/cases/${id}`, payload)
          : api.post("/train/cases", payload))
      ).data;
      setData(saved);
      setBaseline(saved);
      setEditing(false);
      let filesSaved = true;
      if (pendingFiles.length) {
        try {
          await uploadPendingCaseFiles(saved.id, pendingFiles);
          setPendingFiles([]);
        } catch {
          filesSaved = false;
          setError(
            "Случай сохранён, но первичные файлы не загрузились. Прикрепите их в блоке первичной документации",
          );
        }
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["train-filter-options"] }),
        queryClient.invalidateQueries({ queryKey: ["dynamicFilterOptions", "train"] }),
      ]);
      await onSaved(saved);
      if (!id && filesSaved) onClose();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  };
  const remove = async () => {
    if (!id || busy) return false;
    setBusy(true);
    setError("");
    try {
      await api.delete(`/train/cases/${id}`);
      await queryClient.invalidateQueries({ queryKey: ["train-cases"] });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["train-filter-options"] }),
        queryClient.invalidateQueries({ queryKey: ["dynamicFilterOptions", "train"] }),
      ]);

      onClose();
      return true;
    } catch (e) {
      setError(message(e));
      return false;
    } finally {
      setBusy(false);
    }
  };
  const cancel = () => {
    if (!id || !editing) {
      close();
      return;
    }
    setData(structuredClone(baseline));
    setEditing(false);
    setError("");
  };

  const addPendingFiles = (files) =>
    setPendingFiles((prev) => [...prev, ...Array.from(files)]);
  const addPendingLink = (file) =>
    setPendingFiles((prev) => [
      ...prev,
      { ...file, existingFileId: file.id, isLink: true, isPending: true },
    ]);
  const removePendingFile = (file) =>
    setPendingFiles((prev) => prev.filter((item) => item !== file));
  const updateDocument = (document, key, value) =>
    setData((d) => ({ ...d, [document]: { ...d[document], [key]: value } }));
  return {
    data,
    setData,
    editing,
    busy,
    error,
    setError,
    pendingFiles,
    addPendingFiles,
    addPendingLink,
    removePendingFile,
    updateWarrantyField: (key, value) =>
      updateDocument("warranty_work", key, value),
    updateWaybillField: (key, value) =>
      updateDocument("waybill_doc", key, value),
    user,
    users: usersQuery.data || [user],
    id,
    update,
    startEdit,
    close,
    save,
    remove,
    cancel,
  };
}
