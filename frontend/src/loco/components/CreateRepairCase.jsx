import { SHARED_LABELS } from "../../constants/labels";
import { useState } from "react";
import {
  CaseFormWindow,
  CaseFormActions,
} from "../../components/shared/CaseFormWindow";

import { useCreateRepairCase } from "../hooks/useCreateRepairCase";
import { useBodyScrollLock } from "../../hooks/useBodyScrollLock";
import { TabButton } from "../../components/Components";
import { CaseHeader } from "../../components/RepairCase/CaseHeader";
import { GeneralInfo } from "../../components/RepairCase/GeneralInfo";
import { FaultyEquipmentBlock } from "../../components/RepairCase/FaultyEquipmentBlock";
import { RepairExecutionBlock } from "../../components/RepairCase/RepairExecutionBlock";
import { WarrantyWork } from "../../components/RepairCase/WarrantyWork";
import { TtnBlocks } from "../../components/RepairCase/TtnBlocks";
import { CaseValidationToast } from "../../components/Toast/CaseValidationToast";
import { ErrorToast } from "../../components/Toast/ErrorToast";
import { CaseDocuments } from "../../components/RepairCase/CaseDocuments";

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
    updateTtnField,
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
    addPendingLink,
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
    } catch {
      // Ошибка уже показана хуком создания случая
    }
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
    <CaseFormWindow
      label="Создание случая"
      overlays={
        <>
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
        </>
      }
    >
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
          label={SHARED_LABELS.general}
        />
        <TabButton
          active={activeTab === "reclamation"}
          onClick={() => setActiveTab("reclamation")}
          label={SHARED_LABELS.warranty}
        />
        <TabButton
          active={activeTab === "movement"}
          onClick={() => setActiveTab("movement")}
          label={SHARED_LABELS.movement}
        />
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
        </div>
      ) : (
        <div className="custom-scrollbar flex-1 overflow-y-auto bg-white p-6">
          {/* Сохраняем загрузку и проверку оборудования при переключении вкладок */}
          <div hidden={activeTab !== "details"} className="space-y-3">
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
              onAddPendingLink={addPendingLink}
            />
          </div>
          {activeTab === "reclamation" && (
            <WarrantyWork
              isEditing={true}
              currentData={formData}
              repairCase={{}}
              updateWarrantyField={updateWarrantyField}
              references={references}
            />
          )}
          {activeTab === "movement" && (
            <TtnBlocks
              isEditing={true}
              ttnData={formData}
              updateField={updateTtnField}
              showError={showError}
              validation={validation}
              references={references}
            />
          )}
        </div>
      )}

      <CaseFormActions
        creating
        editing
        saving={saving}
        uploading={uploading}
        loading={loading}
        onCancel={onClose}
        onSave={onAttemptCreate}
      />
    </CaseFormWindow>
  );
}
