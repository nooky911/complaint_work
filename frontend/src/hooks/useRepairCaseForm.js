import { useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import api from "../api/api";
import { convertCaseToFormData } from "../utils/formatters";
import { useCaseValidation } from "./useCaseValidation";

const getDepth = (item, all) => {
  let depth = 0;
  let curr = item;
  while (curr?.parent_id) {
    curr = all.find((p) => p.id === curr.parent_id);
    if (!curr) break;
    depth++;
  }
  return depth;
};

export const useRepairCaseForm = (repairCase, onUpdate, currentUser) => {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [showError, setShowError] = useState(false);
  const [serverError, setServerError] = useState({ show: false, message: "" });

  const [editData, setEditData] = useState(null);
  const [references, setReferences] = useState(null);
  const [allEquipment, setAllEquipment] = useState([]);
  const [users, setUsers] = useState([]);
  const [faultyHierarchy, setFaultyHierarchy] = useState(null);
  const [equipmentChain, setEquipmentChain] = useState([]);

  const validation = useCaseValidation(editData, faultyHierarchy, allEquipment);

  useEffect(() => {
    if (!isEditing && repairCase) {
      const targetId =
        repairCase.element_equipment?.id || repairCase.component_equipment?.id;

      if (
        targetId &&
        targetId !== equipmentChain[equipmentChain.length - 1]?.id
      ) {
        api
          .get(`/references/equipment-chain/${targetId}`)
          .then((res) => setEquipmentChain(res.data))
          .catch((err) => console.error("Ошибка загрузки цепочки:", err));
      }
    }
  }, [repairCase, isEditing, equipmentChain]);

  const handleEditClick = async () => {
    setLoading(true);
    setShowError(false);
    try {
      const [refsRes, equipRes] = await Promise.all([
        api.get("/references/case-form"),
        api.get("/references/equipment-all-flat"),
      ]);

      const allEquip = equipRes.data;
      setReferences(refsRes.data);
      setAllEquipment(allEquip);

      // Загружаем пользователей, только если superadmin
      if (currentUser?.role === "superadmin") {
        try {
          const usersRes = await api.get("/users/");
          setUsers(usersRes.data || []);
        } catch (err) {
          console.warn("Не удалось загрузить пользователей:", err);
          setUsers([]);
        }
      }

      const targetId =
        repairCase.element_equipment?.id || repairCase.component_equipment?.id;

      if (targetId) {
        const currentLevels = {
          lvl0: null,
          lvl1: null,
          lvl2: null,
          lvl3: null,
          lvl4: null,
        };
        let current = allEquip.find((i) => i.id === targetId);
        while (current) {
          const depth = getDepth(current, allEquip);
          if (depth <= 4) currentLevels[`lvl${depth}`] = current.id;
          current = allEquip.find((p) => p.id === current.parent_id);
        }

        setFaultyHierarchy({
          component: repairCase.component_equipment?.id,
          element: repairCase.element_equipment?.id,
          fullHierarchy: currentLevels,
        });
      }

      setEditData(convertCaseToFormData(repairCase));
      setIsEditing(true);
    } catch (error) {
      console.error("Ошибка загрузки справочников:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field, value) => {
    setEditData((prev) => ({ ...prev, [field]: value }));
  };

  const updateWarrantyField = (field, value) => {
    setEditData((prev) => ({
      ...prev,
      warranty_work: { ...prev.warranty_work, [field]: value },
    }));
  };

  const handleEquipmentSelect = (data) => {
    setFaultyHierarchy(data);
    setEditData((prev) => {
      if (!prev) return prev;
      const { component, element, supplierId } = data;
      const isComponentChanged = prev.component_equipment_id !== component;
      const isElementChanged = prev.element_equipment_id !== element;

      return {
        ...prev,
        component_equipment_id: component,
        element_equipment_id: element,
        malfunction_id:
          isComponentChanged || isElementChanged ? null : prev.malfunction_id,
        supplier_id: supplierId,
      };
    });
  };

  const handleSave = async () => {
    if (validation.hasErrors) {
      setShowError(true);
      return false;
    }

    setSaving(true);
    try {
      const cleanedData = { ...editData };
      
      // Удаляем user_id если пользователь не superadmin
      if (currentUser?.role !== "superadmin") {
        delete cleanedData.user_id;
      }
      const idFields = [
        "repair_type_id",
        "performed_by_id",
        "equipment_owner_id",
        "destination_id",
        "new_component_equipment_id",
        "new_element_equipment_id",
        "regional_center_id",
        "locomotive_model_id",
        "fault_discovered_at_id",
        "malfunction_id",
        "supplier_id",
      ];

      const processObj = (obj) => {
        Object.keys(obj).forEach((key) => {
          const val = obj[key];
          if (idFields.includes(key) || key.includes("date")) {
            if (
              val === "" ||
              val === undefined ||
              (typeof val === "string" && val.includes("_"))
            ) {
              obj[key] = null;
            }
          }
        });
      };

      processObj(cleanedData);
      if (cleanedData.warranty_work) processObj(cleanedData.warranty_work);

      const initialData = convertCaseToFormData(repairCase);
      const payload = getDirtyValues(initialData, cleanedData);

      if (Object.keys(payload).length === 0) {
        setIsEditing(false);
        setSaving(false);
        return true;
      }

      const response = await api.patch(`/cases/${repairCase.id}`, payload);
      onUpdate(response.data);

      await queryClient.invalidateQueries({ queryKey: ["cases"] });

      setIsEditing(false);
      setEditData(null);
      setShowError(false);
      return true;
    } catch (error) {
      console.error("Ошибка при сохранении случая:", error);

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
      return false;
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditData(null);
    setShowError(false);
  };

  const getDirtyValues = (initial, current) => {
    let dirty = {};
    if (!initial || !current) return current;
    Object.keys(current).forEach((key) => {
      const curVal = current[key];
      const initVal = initial[key];
      if (curVal && typeof curVal === "object" && !Array.isArray(curVal)) {
        const diff = getDirtyValues(initVal || {}, curVal);
        if (Object.keys(diff).length > 0) dirty[key] = diff;
      } else if (curVal !== initVal) {
        dirty[key] = curVal;
      }
    });
    return dirty;
  };

  return {
    isEditing,
    loading,
    saving,
    editData,
    references,
    allEquipment,
    users,
    faultyHierarchy,
    equipmentChain,
    validation,
    showError,
    setShowError,
    serverError,
    closeServerError: () => setServerError({ show: false, message: "" }),
    isSaveDisabled: false,
    handleEditClick,
    handleCancelEdit,
    handleSave,
    updateField,
    updateWarrantyField,
    handleEquipmentSelect,
  };
};
