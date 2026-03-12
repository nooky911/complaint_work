import { useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import api from "../api/api";
import { getInitialCaseData } from "../utils/formatters";
import { useCaseValidation } from "./useCaseValidation";
import { useFormReferences } from "./api/index";
import { logger } from "../utils/logger";

export const useCreateRepairCase = (onSuccess, currentUser) => {
  const queryClient = useQueryClient();
  const [saving, setSaving] = useState(false);
  const [pendingFiles, setPendingFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  const [formData, setFormData] = useState({
    ...getInitialCaseData(),
    user_id: null,
  });

  const [faultyHierarchy, setFaultyHierarchy] = useState(null);
  const [showError, setShowError] = useState(false);
  const [serverError, setServerError] = useState({ show: false, message: "" });

  const {
    data: referencesData,
    isLoading: loading,
    error: referencesError,
  } = useFormReferences(currentUser?.role);

  const validation = useCaseValidation(
    formData,
    faultyHierarchy,
    referencesData?.equipment || [],
  );

  // Обработка ошибок
  useEffect(() => {
    if (referencesError) {
      logger.error("Ошибка загрузки справочников:", referencesError);
    }
  }, [referencesError]);

  const addPendingFiles = (fileList) => {
    const newFiles = Array.from(fileList);
    setPendingFiles((prev) => [...prev, ...newFiles]);
  };

  const removePendingFile = (index) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  useEffect(() => {
    if (currentUser?.id && formData.user_id === null) {
      setFormData((prev) => ({
        ...prev,
        user_id: currentUser.id,
      }));
    }
  }, [currentUser, formData.user_id]);

  const updateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const updateWarrantyField = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      warranty_work: { ...prev.warranty_work, [field]: value },
    }));
  };

  const handleEquipmentSelect = (data) => {
    setFaultyHierarchy(data);
    setFormData((prev) => ({
      ...prev,
      component_equipment_id: data.component,
      element_equipment_id: data.element,
      malfunction_id: null,
      supplier_id: data.supplierId || prev.supplier_id,
    }));
  };

  const handleCreate = async () => {
    if (validation.hasErrors) {
      setShowError(true);
      return;
    }

    setSaving(true);
    try {
      const payload = { ...formData };
      const response = await api.post("/cases/", payload);
      const newCaseId = response.data.id;

      if (pendingFiles.length > 0) {
        setUploading(true);
        try {
          const fileFormData = new FormData();
          fileFormData.append("category", "primary");
          pendingFiles.forEach((file) => {
            fileFormData.append("files", file);
          });
          await api.post(
            `/files/cases/${newCaseId}/upload-files`,
            fileFormData,
          );
        } catch (fileError) {
          console.error("Ошибка загрузки файлов, но случай создан:", fileError);
          setServerError({
            show: true,
            message:
              "Случай создан, но файлы не загрузились. Попробуйте загрузить их позже.",
          });
        }
      }

      await queryClient.invalidateQueries({ queryKey: ["cases"] });

      setShowError(false);
      onSuccess();
    } catch (error) {
      console.error("Ошибка при создании случая или загрузке файлов:", error);

      if (error.response?.status === 409) {
        setServerError({
          show: true,
          message: "Этот случай уже имеется в базе. Проверьте список записей",
        });
      } else {
        setServerError({
          show: true,
          message:
            error.response?.data?.detail || "Не удалось сохранить данные",
        });
      }
    } finally {
      setSaving(false);
      setUploading(false);
    }
  };

  return {
    loading,
    saving,
    users: referencesData?.users || [],
    formData,
    references: referencesData?.references,
    allEquipment: referencesData?.equipment || [],
    faultyHierarchy,
    validation,
    showError,
    serverError,
    pendingFiles,
    uploading,
    addPendingFiles,
    removePendingFile,
    handleCreate,
    setShowError,
    updateField,
    updateWarrantyField,
    handleEquipmentSelect,
    closeServerError: () => setServerError({ show: false, message: "" }),
  };
};
