import React, { useState } from "react";
import { Save } from "lucide-react";

import { useCreateRepairCase } from "../hooks/useCreateRepairCase";
import { useBodyScrollLock } from "../hooks/useBodyScrollLock";
import { TabButton } from "./Components";
import { CaseHeader } from "./RepairCase/CaseHeader";
import { GeneralInfo } from "./RepairCase/GeneralInfo";
import { FaultyEquipmentBlock } from "./RepairCase/FaultyEquipmentBlock";
import { RepairExecutionBlock } from "./RepairCase/RepairExecutionBlock";
import { WarrantyWork } from "./RepairCase/WarrantyWork";
import { CaseValidationToast } from "./Toast/CaseValidationToast";
import { ErrorToast } from "./Toast/ErrorToast";
import { CaseDocuments } from "./RepairCase/CaseDocuments";

export function CreateRepairCase({ onClose, onCreated, currentUser }) {
  const [activeTab, setActiveTab] = useState("details");
  const [showToast, setShowToast] = useState(false);

  const {
    loading,
    saving,
    formData,
    users,
    references,
    allEquipment,
    faultyHierarchy,
    updateField,
    updateWarrantyField,
    handleEquipmentSelect,
    validation,
    handleCreate,
    showError,
    setShowError,
    serverError,
    closeServerError,
    pendingFiles,
    uploading,
    addPendingFiles,
    removePendingFile,
  } = useCreateRepairCase(onCreated, currentUser);

  // Блок скролл body когда модальное окно открыто
  useBodyScrollLock(true);

  const onAttemptCreate = async () => {
    if (validation.hasErrors) {
      setShowError(true);
      setShowToast(true);
      return;
    }

    try {
      await handleCreate();
    } catch (err) {}
  };

  // Заглушка для данных при создании нового случая
  const mockCaseForHeader = {
    id: "NEW",
    displayIndex: "Новый",
    status: "Новый случай",
    creator_full_name: currentUser?.full_name || "Вы",
    date_recorded: new Date().toISOString(),
    supplier: null,
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <CaseValidationToast
        show={showToast}
        onClose={() => setShowToast(false)}
        validation={validation}
      />

      <ErrorToast
        show={serverError.show}
        onClose={closeServerError}
        title="Ошибка сервера"
        message={serverError.message}
      />

      <div className="flex max-h-[95vh] w-full max-w-4xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl">
        <CaseHeader
          repairCase={mockCaseForHeader}
          displayId="Новый"
          status={null}
          isEditing={true}
          references={references}
          editData={formData}
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

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
          </div>
        ) : (
          <div className="custom-scrollbar flex-1 overflow-y-auto bg-white p-6">
            {activeTab === "details" ? (
              <div className="space-y-3">
                <GeneralInfo
                  isEditing={true}
                  currentData={formData}
                  repairCase={{}}
                  updateField={updateField}
                  references={references}
                  validation={validation}
                  showError={showError}
                />

                <FaultyEquipmentBlock
                  isEditing={true}
                  repairCase={{}}
                  currentData={formData}
                  updateField={updateField}
                  references={references}
                  allEquipment={allEquipment}
                  handleEquipmentSelect={handleEquipmentSelect}
                  faultyValidation={validation.faultyValidation}
                  validation={validation}
                  showError={showError}
                />

                <RepairExecutionBlock
                  isEditing={true}
                  repairCase={{}}
                  currentData={formData}
                  updateField={updateField}
                  references={references}
                  allEquipment={allEquipment}
                  faultyHierarchy={faultyHierarchy}
                  blockType={validation.blockType}
                  validation={validation}
                  showError={showError}
                />
                <CaseDocuments
                  isEditing={true}
                  pendingFiles={pendingFiles}
                  onAddFiles={addPendingFiles}
                  onRemoveFile={removePendingFile}
                />
              </div>
            ) : (
              <WarrantyWork
                isEditing={true}
                currentData={formData}
                repairCase={{}}
                updateWarrantyField={updateWarrantyField}
                references={references}
              />
            )}
          </div>
        )}

        <div className="flex justify-end gap-3 border-t border-gray-200 bg-gray-50 px-6 py-4">
          <button
            onClick={onClose}
            disabled={saving || uploading}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 disabled:opacity-50"
          >
            Отмена
          </button>
          <button
            onClick={onAttemptCreate}
            disabled={saving || loading || uploading}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white shadow-md transition-all ${
              saving || loading || uploading
                ? "cursor-not-allowed bg-slate-300 opacity-80 shadow-none"
                : "bg-green-600 hover:bg-green-700 active:scale-95"
            }`}
          >
            {uploading ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Загрузка файлов...
              </>
            ) : saving ? (
              "Создание случая..."
            ) : (
              <>
                <Save className="h-4 w-4" /> Создать случай
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
