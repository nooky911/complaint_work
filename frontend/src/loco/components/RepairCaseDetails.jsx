import { SHARED_LABELS } from "../../constants/labels";
import { useState, useEffect, useRef } from "react";
import { Edit, Save, X, Trash2 } from "lucide-react";
import { useEditFileUploads } from "../../hooks/useUnifiedFileManagement";
import { DeleteConfirmDialog } from "../../components/common/DeleteConfirmDialog";

import { CaseDeleteConfirmation } from "../../components/shared/CaseDeleteConfirmation";
import api from "../../api/api";
import { isCaseLockedByOther } from "../../utils/caseLock";
import { formatFullName } from "../../utils/formatters";
import { useRepairCaseForm } from "../hooks/useRepairCaseForm";
import { useBodyScrollLock } from "../../hooks/useBodyScrollLock";
import { CaseDocuments } from "../../components/RepairCase/CaseDocuments";
import { TabButton } from "../../components/Components";
import { getStatusConfig } from "../../utils/statusHelpers";
import { CaseHeader } from "../../components/RepairCase/CaseHeader";
import { GeneralInfo } from "../../components/RepairCase/GeneralInfo";
import { FaultyEquipmentBlock } from "../../components/RepairCase/FaultyEquipmentBlock";
import { RepairExecutionBlock } from "../../components/RepairCase/RepairExecutionBlock";
import { WarrantyWork } from "../../components/RepairCase/WarrantyWork";
import { TtnBlocks } from "../../components/RepairCase/TtnBlocks";
import { CaseValidationToast } from "../../components/Toast/CaseValidationToast";
import { ErrorToast } from "../../components/Toast/ErrorToast";

export function RepairCaseDetails({
  repairCase,
  onClose,
  onUpdate,
  onDelete,
  currentUser,
  caseIndex,
}) {
  const restricted = !!currentUser?.restricted_access;
  const [activeTab, setActiveTab] = useState("details");
  const [showToast, setShowToast] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [serverError, setServerError] = useState({ show: false, message: "" });
  const scrollContainerRef = useRef(null);

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0;
    }
  }, [activeTab]);

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
  } = useRepairCaseForm(repairCase, onUpdate, currentUser);

  const fileSession = useEditFileUploads({
    caseId: repairCase?.id,
    editing: isEditing,
    disabled: saving,
    onCancel: handleCancelEdit,
    onClose: async () => {
      if (isEditing) await handleCancelEdit();
      onClose();
    },
    onError: (message) => setServerError({ show: true, message }),
  });

  const partnerIds = currentUser?.partner_ids || [];

  const isPartnerAccess = partnerIds.includes(repairCase.user_id);

  const canEdit =
    currentUser?.role === "superadmin" ||
    (currentUser?.role !== "viewer" &&
      (repairCase.user_id === currentUser?.id || isPartnerAccess));

  // Проверка блокировки другими пользователями
  const [lockClock, setLockClock] = useState(Date.now);
  useEffect(() => {
    const timer = setInterval(() => setLockClock(Date.now()), 10000);
    return () => clearInterval(timer);
  }, []);
  const isLockedByOther = isCaseLockedByOther(
    repairCase,
    currentUser?.id,
    lockClock,
  );
  const lockerName = repairCase.locked_by?.full_name
    ? formatFullName(repairCase.locked_by.full_name)
    : "Другой пользователь";

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
    if (fileSession.busy) return;
    if (validation.hasErrors) {
      setShowError(true);
      setShowToast(true);
      return;
    }
    try {
      const success = await handleSave();
      if (success) {
        setShowToast(false);
      }
    } catch (err) {
      console.error("Ошибка при сохранении:", err);
    }
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
      setServerError({
        show: true,
        message: error.response?.data?.detail || "Не удалось удалить случай",
      });
      setShowDeleteConfirm(false);
    } finally {
      setDeleting(false);
    }
  };

  const status = getStatusConfig(repairCase);
  const displayId = caseIndex || repairCase.id;
  const currentData = isEditing ? editData : repairCase;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      {isEditing && (
        <CaseValidationToast
          show={showToast}
          onClose={() => setShowToast(false)}
          validation={validation}
        />
      )}

      {serverError.show && (
        <ErrorToast
          show={serverError.show}
          onClose={() => setServerError({ show: false, message: "" })}
          title="Ошибка"
          message={serverError.message}
        />
      )}

      <div
        data-case-window
        className="flex max-h-[95vh] w-full max-w-4xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <CaseHeader
          repairCase={repairCase}
          displayId={displayId}
          status={restricted ? null : status}
          isEditing={isEditing}
          references={references}
          editData={editData}
          onClose={fileSession.requestClose}
          currentUser={currentUser}
          users={users}
          updateField={updateField}
        />

        <div className="flex gap-8 border-b border-gray-200 bg-gray-50 px-6 pt-2">
          <TabButton
            active={activeTab === "details"}
            onClick={() => setActiveTab("details")}
            label={SHARED_LABELS.general}
          />
          <TabButton
            active={activeTab === "reclamation"}
            onClick={() => setActiveTab("reclamation")}
            label={SHARED_LABELS.warranty}
          />
          {!restricted && (
            <TabButton
              active={activeTab === "movement"}
              onClick={() => setActiveTab("movement")}
              label={SHARED_LABELS.movement}
            />
          )}
        </div>

        <div
          ref={scrollContainerRef}
          className="custom-scrollbar flex-1 overflow-y-auto bg-white p-6"
          style={{ willChange: "transform" }}
        >
          {/* Сохраняем загрузку и проверку оборудования при переключении вкладок */}
          <div hidden={activeTab !== "details"} className="space-y-3">
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
            {!restricted && (
              <CaseDocuments
                caseId={repairCase.id}
                isEditing={isEditing}
                onFilesUploaded={fileSession.recordUploads}
              />
            )}
          </div>
          {activeTab === "reclamation" && (
            <WarrantyWork
              isEditing={isEditing}
              currentData={currentData}
              repairCase={repairCase}
              updateWarrantyField={updateWarrantyField}
              references={references}
              caseId={repairCase.id}
              onFilesUploaded={fileSession.recordUploads}
            />
          )}
          {!restricted && activeTab === "movement" && (
            <TtnBlocks
              isEditing={isEditing}
              ttnData={currentData}
              updateField={updateField}
              showError={showError}
              validation={validation}
              references={references}
              caseId={repairCase.id}
              onFilesUploaded={fileSession.recordUploads}
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
                  onClick={fileSession.requestCancel}
                  disabled={saving || fileSession.busy}
                  className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 disabled:opacity-50"
                >
                  <X className="h-4 w-4" /> Отмена
                </button>
                <button
                  onClick={onAttemptSave}
                  disabled={saving || fileSession.busy}
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
                  onClick={fileSession.requestClose}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
                >
                  Закрыть
                </button>
                {canEdit && (
                  <div className="group relative">
                    <button
                      onClick={handleEditClick}
                      disabled={loading || isLockedByOther}
                      className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white shadow-md transition-all ${
                        isLockedByOther
                          ? "cursor-not-allowed bg-gray-400"
                          : "bg-[#0064fe] hover:bg-blue-700 active:scale-95"
                      } disabled:opacity-50`}
                    >
                      <Edit className="h-4 w-4" /> Редактировать
                    </button>
                    {isLockedByOther && (
                      <div className="absolute right-0 bottom-full mb-2 hidden rounded bg-black/80 px-2 py-1 text-[10px] whitespace-nowrap text-white group-hover:block">
                        Сейчас редактирует: {lockerName}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      <DeleteConfirmDialog {...fileSession.confirmation} />
      <CaseDeleteConfirmation
        show={showDeleteConfirm}
        deleting={deleting}
        onCancel={() => setShowDeleteConfirm(false)}
        onConfirm={confirmDelete}
      />
    </div>
  );
}
