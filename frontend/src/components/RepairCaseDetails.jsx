import React, { useState, useEffect } from "react";
import { Edit, Save, X, Trash2, AlertTriangle } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import api from "../api/api";
import { useRepairCaseForm } from "../hooks/useRepairCaseForm";
import { useBodyScrollLock } from "../hooks/useBodyScrollLock";
import { CaseDocuments } from "./RepairCase/CaseDocuments";
import { TabButton } from "./Components";
import { getStatusConfig } from "../utils/statusHelpers";
import { CaseHeader } from "./RepairCase/CaseHeader";
import { GeneralInfo } from "./RepairCase/GeneralInfo";
import { FaultyEquipmentBlock } from "./RepairCase/FaultyEquipmentBlock";
import { RepairExecutionBlock } from "./RepairCase/RepairExecutionBlock";
import { WarrantyWork } from "./RepairCase/WarrantyWork";
import { CaseValidationToast } from "./Toast/CaseValidationToast";
import { ErrorToast } from "./Toast/ErrorToast";

export function RepairCaseDetails({
  repairCase,
  onClose,
  onUpdate,
  onDelete,
  currentUser,
  caseIndex,
}) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("details");
  const [showToast, setShowToast] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [uploadedDuringEditIds, setUploadedDuringEditIds] = useState([]);

  const {
    isEditing,
    loading,
    saving,
    editData,
    references,
    allEquipment,
    users,
    faultyHierarchy,
    validation,
    handleEditClick,
    handleCancelEdit,
    handleSave,
    updateField,
    updateWarrantyField,
    handleEquipmentSelect,
    showError,
    setShowError,
    serverError,
    closeServerError,
  } = useRepairCaseForm(repairCase, onUpdate, currentUser);

  const canEdit =
    currentUser?.role === "superadmin" ||
    (currentUser?.role !== "viewer" && repairCase.user_id === currentUser?.id);

  // Блок скролл body только когда модальное окно реально открыто
  useBodyScrollLock(!!repairCase);

  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (isEditing) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isEditing]);

  if (!repairCase) return null;

  const onAttemptSave = async () => {
    if (validation.hasErrors) {
      setShowError(true);
      setShowToast(true);
      return;
    }
    try {
      const success = await handleSave();
      if (success) {
        setUploadedDuringEditIds([]);
        setShowToast(false);
      }
    } catch (err) {
      console.error("Ошибка при сохранении:", err);
    }
  };

  const onFilesUploadedDuringEdit = (uploadedFiles) => {
    const filesArray = Array.isArray(uploadedFiles) ? uploadedFiles : [];
    const ids = filesArray.map((f) => f?.id).filter(Boolean);
    if (ids.length === 0) return;
    setUploadedDuringEditIds((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => next.add(id));
      return Array.from(next);
    });
  };

  const onCancelEdit = async () => {
    console.log(
      "Отмена редактирования, удаление файлов:",
      uploadedDuringEditIds,
    );

    if (uploadedDuringEditIds.length > 0) {
      try {
        const results = await Promise.allSettled(
          uploadedDuringEditIds.map((fileId) => {
            console.log("Удаляем файл:", fileId);
            return api.delete(`/files/${fileId}`);
          }),
        );
        console.log("Результаты удаления:", results);
      } catch (err) {
        console.error("Ошибка отката загруженных файлов при отмене:", err);
      }
    }

    console.log("Обновляем кеш...");
    queryClient.invalidateQueries({ queryKey: ["files", repairCase.id] });
    queryClient.invalidateQueries({
      queryKey: ["filesGrouped", repairCase.id],
    });
    queryClient.invalidateQueries({
      queryKey: ["warrantyFiles", repairCase.id],
    });
    queryClient.refetchQueries({ queryKey: ["files", repairCase.id] });
    queryClient.refetchQueries({ queryKey: ["filesGrouped", repairCase.id] });

    setUploadedDuringEditIds([]);
    handleCancelEdit();
  };

  const confirmDelete = async () => {
    setDeleting(true);
    try {
      await api.delete(`/cases/${repairCase.id}`);
      setShowDeleteConfirm(false);
      if (onDelete) {
        onDelete(repairCase.id);
      }
      onClose();
    } catch (error) {
      console.error("Ошибка при удалении:", error);
    } finally {
      setDeleting(false);
    }
  };

  const status = getStatusConfig(repairCase);
  const displayId = caseIndex || repairCase.id;
  const currentData = isEditing ? editData : repairCase;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <ErrorToast
        show={serverError.show}
        onClose={closeServerError}
        title="Ошибка сервера"
        message={serverError.message}
      />

      <CaseValidationToast
        show={showToast}
        onClose={() => setShowToast(false)}
        validation={validation}
      />

      <div
        className="flex max-h-[95vh] w-full max-w-4xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <CaseHeader
          repairCase={repairCase}
          displayId={displayId}
          status={status}
          isEditing={isEditing}
          references={references}
          editData={editData}
          onClose={onClose}
          currentUser={currentUser}
          users={users}
          updateField={updateField}
        />

        <div className="flex gap-8 border-b border-gray-200 bg-gray-50 px-6 pt-2">
          <TabButton
            active={activeTab === "details"}
            onClick={() => setActiveTab("details")}
            label="ОСНОВНЫЕ ДАННЫЕ"
          />
          <TabButton
            active={activeTab === "reclamation"}
            onClick={() => setActiveTab("reclamation")}
            label="РЕКЛАМАЦИЯ"
          />
        </div>

        <div className="custom-scrollbar flex-1 overflow-y-auto bg-white p-6">
          {activeTab === "details" ? (
            <div className="space-y-3">
              <GeneralInfo
                isEditing={isEditing}
                currentData={currentData}
                repairCase={repairCase}
                updateField={updateField}
                references={references}
                showError={showError}
                validation={validation}
              />
              <FaultyEquipmentBlock
                isEditing={isEditing}
                repairCase={repairCase}
                currentData={currentData}
                updateField={updateField}
                references={references}
                allEquipment={allEquipment}
                handleEquipmentSelect={handleEquipmentSelect}
                isHardBlocked={validation.isRepairTypeBlocked}
                showError={showError}
                validation={validation}
                faultyValidation={validation.faultyValidation}
              />
              <RepairExecutionBlock
                isEditing={isEditing}
                repairCase={repairCase}
                currentData={currentData}
                updateField={updateField}
                references={references}
                allEquipment={allEquipment}
                faultyHierarchy={faultyHierarchy}
                blockType={validation.blockType}
                showError={showError}
                validation={validation}
              />
              <CaseDocuments
                caseId={repairCase.id}
                isEditing={isEditing}
                onFilesUploaded={onFilesUploadedDuringEdit}
              />
            </div>
          ) : (
            <WarrantyWork
              isEditing={isEditing}
              currentData={currentData}
              repairCase={repairCase}
              updateWarrantyField={updateWarrantyField}
              references={references}
              caseId={repairCase.id}
              onFilesUploaded={onFilesUploadedDuringEdit}
            />
          )}
        </div>

        <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 px-6 py-4">
          <div>
            {!isEditing && canEdit && (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4" /> Удалить случай
              </button>
            )}
          </div>

          <div className="flex gap-3">
            {isEditing ? (
              <>
                <button
                  onClick={onCancelEdit}
                  disabled={saving}
                  className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 disabled:opacity-50"
                >
                  <X className="h-4 w-4" /> Отмена
                </button>
                <button
                  onClick={onAttemptSave}
                  disabled={saving}
                  className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white shadow-md transition-all ${
                    saving
                      ? "cursor-not-allowed bg-slate-300 opacity-80 shadow-none"
                      : "bg-green-600 hover:bg-green-700 active:scale-95"
                  }`}
                >
                  {saving ? (
                    "Сохранение..."
                  ) : (
                    <>
                      <Save className="h-4 w-4" /> Сохранить
                    </>
                  )}
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={onClose}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
                >
                  Закрыть
                </button>
                {canEdit && (
                  <button
                    onClick={handleEditClick}
                    disabled={loading}
                    className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-md transition-colors hover:bg-blue-700 disabled:opacity-50"
                  >
                    <Edit className="h-4 w-4" /> Редактировать
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {showDeleteConfirm && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center gap-3 text-red-600">
              <AlertTriangle className="h-6 w-6" />
              <h3 className="text-lg font-bold">
                Вы точно хотите удалить случай?
              </h3>
            </div>
            <p className="mb-6 text-sm text-gray-600">
              Все данные удалятся без возможности восстановления.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleting}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
              >
                Нет
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleting}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-md hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? "Удаление..." : "Да, удалить"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
