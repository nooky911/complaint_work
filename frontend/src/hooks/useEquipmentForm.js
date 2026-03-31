import { useState, useCallback } from "react";

export const useEquipmentForm = () => {
  const [detectedSupplierId, setDetectedSupplierId] = useState(null);
  const [originalSupplierId, setOriginalSupplierId] = useState(null);
  const [hasSupplierChanges, setHasSupplierChanges] = useState(false);
  const [canEditSupplier, setCanEditSupplier] = useState(false);
  const [currentData, setCurrentData] = useState({});

  const updateField = useCallback(
    (field, value) => {
      setCurrentData((prev) => ({ ...prev, [field]: value }));

      if (field === "supplier_id") {
        setHasSupplierChanges(value !== originalSupplierId);
      }
    },
    [originalSupplierId],
  );

  const handleEquipmentSelect = useCallback((equipmentData) => {
    if (equipmentData && (equipmentData.component || equipmentData.element)) {
      const equipmentId = equipmentData.element || equipmentData.component;
      const supplierId = equipmentData.supplier_id || equipmentData.supplierId || null;
      
      setCurrentData((prev) => ({
        ...prev,
        id: equipmentId,
        supplier_id: supplierId,
      }));

      setCanEditSupplier(equipmentData.level >= 3);

      setDetectedSupplierId(supplierId);
      setOriginalSupplierId(supplierId);
      setHasSupplierChanges(false);
    } else {
      setCurrentData((prev) => ({
        ...prev,
        id: null,
        supplier_id: null,
      }));
      setCanEditSupplier(false);
      setDetectedSupplierId(null);
      setOriginalSupplierId(null);
      setHasSupplierChanges(false);
    }
  }, []);

  const handleCancelSupplierChanges = useCallback(() => {
    setCurrentData((prev) => ({
      ...prev,
      supplier_id: originalSupplierId,
    }));
    setHasSupplierChanges(false);
  }, [originalSupplierId]);

  const resetForm = useCallback(() => {
    setCurrentData({});
    setDetectedSupplierId(null);
    setOriginalSupplierId(null);
    setHasSupplierChanges(false);
    setCanEditSupplier(false);
  }, []);

  return {
    detectedSupplierId,
    originalSupplierId,
    hasSupplierChanges,
    canEditSupplier,
    currentData,

    updateField,
    handleEquipmentSelect,
    handleCancelSupplierChanges,
    resetForm,
    setCurrentData,
    setCanEditSupplier,
    setOriginalSupplierId,
  };
};
