import { useEffect, useRef, useState } from "react";
import { useBodyScrollLock } from "../../hooks/useBodyScrollLock";
import { CaseHeader } from "../../components/RepairCase/CaseHeader";
import { GeneralInfo } from "../../components/RepairCase/GeneralInfo";
import { FaultyEquipmentBlock } from "../../components/RepairCase/FaultyEquipmentBlock";
import { RepairExecutionBlock } from "../../components/RepairCase/RepairExecutionBlock";
import {
  CaseFormWindow,
  CaseFormActions,
} from "../../components/shared/CaseFormWindow";
import { TabButton } from "../../components/Components";
import { CaseValidationToast } from "../../components/Toast/CaseValidationToast";
import { CaseDeleteConfirmation } from "../../components/shared/CaseDeleteConfirmation";
import { ErrorToast } from "../../components/Toast/ErrorToast";
import { WarrantyWork } from "../../components/RepairCase/WarrantyWork";
import { TtnBlocks } from "../../components/RepairCase/TtnBlocks";
import { CaseDocuments } from "../../components/RepairCase/CaseDocuments";

import { useEditFileUploads } from "../../hooks/useUnifiedFileManagement";
import { DeleteConfirmDialog } from "../../components/common/DeleteConfirmDialog";

import { getStatusConfig } from "../../utils/statusHelpers";
import { useCaseValidation } from "../../hooks/useCaseValidation";
import { useTrainCaseForm } from "../hooks/useTrainCaseForm";
import { useTrainPassport } from "../hooks/useTrainPassport";
import { useTrainEquipment } from "../hooks/useTrainEquipment";
import { TrainIdentityFields } from "./TrainIdentityFields";
import {
  TrainEquipmentEditor,
  TrainReplacementEditor,
} from "./TrainEquipmentEditor";

/** Собирает поездные адаптеры и общие блоки окна случая */
export default function TrainCaseForm({
  initial,
  references: sourceReferences,
  onClose,
  onSaved,
}) {
  useBodyScrollLock();
  const r = { ...sourceReferences, repair_types: (sourceReferences.repair_types || []).filter((item) => item.id !== 8) };
  const form = useTrainCaseForm({ initial, onClose, onSaved });
  const query = useTrainPassport(form.data, form.setData);
  const equipment = useTrainEquipment(form, r, query.passport);
  const {
    data,
    editing,
    busy,
    error,
    setError,
    pendingFiles,
    addPendingFiles,
    addPendingLink,
    removePendingFile,
    updateWarrantyField,
    updateWaybillField,
    user,
    id,
    update,
    startEdit,
    close,
    save,
    cancel,
  } = form;
  const fileSession = useEditFileUploads({ caseId: id, editing, disabled: busy,
    onCancel: cancel, onClose: close, onError: setError });
  const { prettyEquipment, levels, viewData, headerData, changeRepairType } =
    equipment;
  const validation = useCaseValidation(
    data,
    levels,
    r.equipment,
    undefined,
    "train",
  );
  const [showError, setShowError] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [tab, setTab] = useState("details");
  const scrollRef = useRef(null);
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [tab]);
  return (
    <CaseFormWindow
      label={id ? "Поездной случай" : "Создание поездного случая"}
      overlays={
        <>
          <DeleteConfirmDialog {...fileSession.confirmation} />
          <CaseDeleteConfirmation
            show={showDeleteConfirm}
            deleting={busy}
            onCancel={() => setShowDeleteConfirm(false)}
            onConfirm={async () => {
              if (!(await form.remove())) setShowDeleteConfirm(false);
            }}
          />
          <CaseValidationToast
            train
            show={showError}
            onClose={() => setShowError(false)}
            validation={validation}
          />
          <ErrorToast
            show={!!error}
            onClose={() => setError("")}
            title="Ошибка"
            message={error}
          />
        </>
      }
    >
      <CaseHeader
        repairCase={viewData}
        displayId={id ? data.display_number || id : "Новый"}
        status={id ? getStatusConfig(viewData) : null}
        isEditing={editing}
        references={r}
        editData={headerData}
        onClose={fileSession.requestClose}
        currentUser={user}
        users={form.users}
        updateField={update}
      />
      <div className="flex gap-8 border-b border-gray-200 bg-gray-50 px-6 pt-2">
        {[
          ["details", "ОСНОВНЫЕ ДАННЫЕ"],
          ["warranty", "РЕКЛАМАЦИЯ"],
          ["movement", "ПЕРЕДВИЖЕНИЕ"],
        ].map(([key, label]) => (
          <TabButton
            key={key}
            active={tab === key}
            onClick={() => setTab(key)}
            label={label}
          />
        ))}
      </div>
      <div
        ref={scrollRef}
        className="custom-scrollbar flex-1 overflow-y-auto bg-white p-6"
      >
        <div hidden={tab !== "details"} className="space-y-3">
          <GeneralInfo
            title="Поезд и место"
            identityFields={
              <TrainIdentityFields
                form={form}
                references={r}
                passport={query}
                validation={validation}
                showError={showError}
              />
            }
            isEditing={editing}
            currentData={data}
            repairCase={viewData}
            updateField={update}
            references={r}
            validation={validation}
            showError={showError}
          />
          <FaultyEquipmentBlock
            isEditing={editing}
            repairCase={viewData}
            currentData={data}
            updateField={update}
            references={r}
            allEquipment={prettyEquipment}
            validation={validation}
            showError={showError}
            editor={
              <TrainEquipmentEditor
                form={form}
                equipment={equipment}
                validation={validation}
                showError={showError}
                references={r}
              />
            }
          />
          <RepairExecutionBlock
            isEditing={editing}
            currentData={editing ? data : viewData}
            updateField={update}
            references={r}
            allEquipment={prettyEquipment}
            faultyHierarchy={{ fullHierarchy: levels }}
            validation={validation}
            showError={showError}
            equipmentAdapter={{
              isSelected: !!data.train.equipment_id,
              onRepairTypeChange: changeRepairType,
              replacement: (
                <TrainReplacementEditor form={form} equipment={equipment} />
              ),
            }}
          />
          <CaseDocuments
            caseId={id || null}
            isEditing={editing}
            pendingFiles={pendingFiles}
            onFilesUploaded={fileSession.recordUploads}
            onAddFiles={addPendingFiles}
            onAddPendingLink={addPendingLink}
            onRemoveFile={removePendingFile}
          />
        </div>
        {tab === "warranty" && (
          <WarrantyWork
            train
            isEditing={editing}
            currentData={data}
            repairCase={data}
            references={r}
            caseId={id}
            onFilesUploaded={fileSession.recordUploads}
            updateWarrantyField={updateWarrantyField}
          />
        )}
        {tab === "movement" && (
          <TtnBlocks
            isEditing={editing}
            ttnData={data}
            references={r}
            caseId={id}
            onFilesUploaded={fileSession.recordUploads}
            updateField={updateWaybillField}
          />
        )}
      </div>
      <CaseFormActions
        creating={!id}
        editing={editing}
        saving={busy && editing}
        loading={busy || fileSession.busy}
        uploading={fileSession.busy}
        canEdit={data.can_edit}
        onCancel={fileSession.requestCancel}
        onSave={() => {
          if (fileSession.busy) return;
          if (validation.hasErrors) {
            setShowError(true);
          } else if (equipment.selectionError)
            setError(equipment.selectionError);
          else if (
            equipment.replacementKey &&
            data.train.passport_node_ids.length &&
            (equipment.replacementQuery.isFetching ||
              equipment.replacementQuery.isError ||
              data._passport_replacement_invalid !== false)
          )
            setError("Дождитесь расчёта и проверьте установленный состав");
          else save(equipment.replacementLinks);
        }}
        onEdit={startEdit}
        onDelete={() => setShowDeleteConfirm(true)}
      />
    </CaseFormWindow>
  );
}
