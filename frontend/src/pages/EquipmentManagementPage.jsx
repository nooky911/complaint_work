import React, { useCallback, useMemo } from "react";
import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { SimpleEquipmentEditor } from "../components/SimpleEquipmentEditor";
import { EditableInlineControl } from "../components/inputs";
import { SelectField } from "../components/inputs";
import { useToast } from "../hooks/useToast";
import { EquipmentValidation } from "../utils/equipmentValidation";
import { ErrorToast } from "../components/Toast/ErrorToast";
import { useAuth } from "../context/AuthContext";

// Новые хуки
import { useEquipmentData } from "../hooks/useEquipmentData";
import { useEquipmentForm } from "../hooks/useEquipmentForm";
import {
  useCreateSupplier,
  useUpdateSupplier,
  useUpdateEquipment,
} from "../hooks/useEquipmentMutations";

export default function EquipmentManagementPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const {
    allEquipment = [],
    references = {},
    allSuppliers = [],
    loading,
  } = useEquipmentData() || {};
  const {
    toasts = [],
    addToast,
    removeToast,
    showError,
    showSuccess,
  } = useToast() || {};
  const {
    currentData,
    hasSupplierChanges,
    canEditSupplier,
    updateField,
    handleEquipmentSelect,
    handleCancelSupplierChanges,
    setOriginalSupplierId,
  } = useEquipmentForm();

  // Мутации
  const createSupplierMutation = useCreateSupplier();
  const updateSupplierMutation = useUpdateSupplier();
  const updateEquipmentMutation = useUpdateEquipment();

  // Обработчики с использованием мутаций
  const handleCreateSupplier = useCallback(
    async (name) => {
      const validation = EquipmentValidation.validateCreateSupplier(
        name,
        allSuppliers,
      );
      if (!validation.isValid) {
        validation.errors.forEach((error) => {
          addToast({
            type: error.type,
            title: "Ошибка создания",
            message: error.message,
          });
        });
        return;
      }

      try {
        const result = await createSupplierMutation.mutateAsync(name);
        showSuccess("Успешно", `Поставщик "${name}" создан`);

        // Автоматически выбираем нового поставщика
        if (result?.response?.data?.id) {
          updateField("supplier_id", result.response.data.id);
        }
      } catch (error) {
        console.error("Ошибка при создании:", error);

        if (error.response?.status === 200) {
          addToast({
            type: "info",
            title: "Информация",
            message: `Поставщик "${name}" уже существует в справочнике`,
          });
        } else {
          const errorMessage =
            error.response?.data?.detail ||
            "Произошла ошибка при создании поставщика";
          showError("Ошибка создания", errorMessage);
        }
      }
    },
    [
      allSuppliers,
      addToast,
      showSuccess,
      showError,
      createSupplierMutation,
      updateField,
    ],
  );

  const handleSaveSupplierName = useCallback(
    async (newName) => {
      const validation = EquipmentValidation.checkDuplicateSupplier(
        newName,
        allSuppliers,
        currentData.supplier_id,
      );
      if (!validation.isValid) {
        addToast({
          type: validation.type,
          title: "Ошибка редактирования",
          message: validation.message,
        });
        return;
      }

      try {
        await updateSupplierMutation.mutateAsync({
          id: currentData.supplier_id,
          name: newName,
        });
        showSuccess("Успешно", `Поставщик "${newName}" обновлен`);
      } catch (error) {
        console.error("Ошибка при обновлении поставщика:", error);
        const errorMessage =
          error.response?.data?.detail ||
          "Произошла ошибка при обновлении поставщика";
        showError("Ошибка редактирования", errorMessage);
      }
    },
    [
      allSuppliers,
      currentData.supplier_id,
      addToast,
      showSuccess,
      showError,
      updateEquipmentMutation,
      setOriginalSupplierId,
    ],
  );

  const referencesData = useMemo(
    () => ({
      malfunctions: references?.malfunctions || [],
      equipment_malfunctions: references?.equipment_malfunctions || [],
      suppliers: allSuppliers,
    }),
    [references, allSuppliers],
  );

  // Проверка доступа - только для superadmin
  if (user?.role !== "superadmin") {
    return (
      <div className="flex h-full items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="mb-4 text-2xl font-bold text-red-600">
            Доступ запрещен
          </h1>
          <p className="mb-6 text-gray-600">
            Только пользователи с правами superadmin могут управлять
            оборудованием.
          </p>
          <button
            onClick={() => navigate("/")}
            className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-colors hover:bg-blue-700"
          >
            Вернуться на главную
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Заголовок страницы */}
      <div className="flex items-center gap-4 border-b border-gray-200 bg-white px-6 py-4">
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-gray-600 transition-colors hover:text-gray-900"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Назад</span>
        </button>
        <h1 className="text-xl font-semibold text-gray-900">
          Управление оборудованием
        </h1>
      </div>

      <div className="flex-1 overflow-auto bg-gray-50 p-6">
        <div className="mx-auto max-w-4xl">
          {loading ? (
            <div className="flex h-64 animate-pulse flex-col items-center justify-center gap-4 rounded-lg border border-gray-200 bg-white p-6">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
              <span className="text-xs font-black tracking-widest text-slate-400 uppercase">
                Загрузка оборудования...
              </span>
            </div>
          ) : (
            <div className="rounded-lg border border-gray-200 bg-white p-6">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Оборудование
                </h3>

                {/* Поставщик */}
                <div className="w-[400px]">
                  <EditableInlineControl
                    itemId={currentData.supplier_id}
                    label="Поставщик"
                    currentName={(() => {
                      if (!currentData.supplier_id || !allSuppliers?.length)
                        return "";
                      const found = (allSuppliers || []).find(
                        (s) => String(s.id) === String(currentData.supplier_id),
                      );
                      return found?.supplier_name || found?.name || "";
                    })()}
                    onSave={handleSaveSupplierName}
                    onAdd={handleCreateSupplier}
                    disabled={!canEditSupplier}
                  >
                    <SelectField
                      label=""
                      value={currentData.supplier_id}
                      options={(allSuppliers || []).map((s) => ({
                        id: s.id,
                        name: s.supplier_name || s.name,
                      }))}
                      onChange={(val) => updateField("supplier_id", val)}
                      placeholder="—"
                      isEditing={true}
                      disabled={!canEditSupplier}
                    />
                  </EditableInlineControl>
                </div>
              </div>

              {/* Редактор иерархии оборудования */}
              <SimpleEquipmentEditor
                isEditing={true}
                currentId={currentData.id || null}
                onSelect={handleEquipmentSelect}
                currentData={currentData}
                updateField={updateField}
                references={referencesData}
                allEquipment={allEquipment}
                disableAutoFill={true}
              />

              {/* Кнопки сохранения/отмены для поставщика */}
              {hasSupplierChanges && (
                <div className="mt-4 flex justify-end gap-2">
                  <button
                    onClick={handleCancelSupplierChanges}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
                  >
                    Отменить
                  </button>
                  <button
                    onClick={async () => {
                      if (!currentData.supplier_id) return;
                      try {
                        await updateEquipmentMutation.mutateAsync({
                          id: currentData.id,
                          supplier_id: currentData.supplier_id,
                        });
                        showSuccess(
                          "Успешно",
                          "Поставщик привязан к оборудованию",
                        );
                        // Сбрасываем состояние изменений после успешного сохранения
                        setOriginalSupplierId(currentData.supplier_id);
                      } catch (error) {
                        console.error("Ошибка при обновлении:", error);
                        const errorMessage =
                          error.response?.data?.detail || "Произошла ошибка";
                        showError("Ошибка", errorMessage);
                      }
                    }}
                    disabled={updateEquipmentMutation.isPending}
                    className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                  >
                    {updateEquipmentMutation.isPending
                      ? "Сохранение..."
                      : "Сохранить"}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Контейнер для тостов */}
      {(toasts || []).map((toast) => (
        <ErrorToast
          key={toast.id}
          show={true}
          title={toast.title}
          message={toast.message}
          type={toast.type}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  );
}
