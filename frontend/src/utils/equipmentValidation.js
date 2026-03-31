// Утилиты для валидации операций с оборудованием на фронтенде

export const EquipmentValidation = {
  // Проверка дубликатов оборудования
  checkDuplicateEquipment: (equipmentName, parentId, allEquipment) => {
    const duplicate = allEquipment.find(
      (eq) => eq.name === equipmentName && eq.parent_id === parentId,
    );

    if (duplicate) {
      return {
        isValid: false,
        message: `Оборудование "${equipmentName}" уже существует в этой категории`,
        type: "error",
      };
    }
    return { isValid: true };
  },

  // Проверка дубликатов поставщиков
  checkDuplicateSupplier: (
    supplierName,
    allSuppliers,
    currentSupplierId = null,
  ) => {
    const duplicate = allSuppliers.find(
      (supp) =>
        supp.supplier_name === supplierName && supp.id !== currentSupplierId,
    );

    if (duplicate) {
      return {
        isValid: false,
        message: `Поставщик "${supplierName}" уже есть в справочнике`,
        type: "error",
      };
    }
    return { isValid: true };
  },

  // Проверка дубликатов неисправностей
  checkDuplicateMalfunction: (
    malfunctionName,
    allMalfunctions,
    currentMalfunctionId = null,
  ) => {
    const duplicate = allMalfunctions.find(
      (malf) =>
        malf.defect_name === malfunctionName &&
        malf.id !== currentMalfunctionId,
    );

    if (duplicate) {
      return {
        isValid: false,
        message: `Неисправность "${malfunctionName}" уже есть в справочнике`,
        type: "error",
      };
    }
    return { isValid: true };
  },

  // Валидация пустых полей
  checkEmptyField: (value, fieldName) => {
    if (!value || value.trim() === "") {
      return {
        isValid: false,
        message: `Поле "${fieldName}" не может быть пустым`,
        type: "warning",
      };
    }
    return { isValid: true };
  },

  // Валидация длины названия
  checkNameLength: (name, maxLength = 100) => {
    if (name.length > maxLength) {
      return {
        isValid: false,
        message: `Название не должно превышать ${maxLength} символов`,
        type: "warning",
      };
    }
    return { isValid: true };
  },

  // Комплексная валидация создания оборудования
  validateCreateEquipment: (equipmentName, parentId, allEquipment) => {
    const results = [];

    // Проверка пустого названия
    const emptyCheck = EquipmentValidation.checkEmptyField(
      equipmentName,
      "Название оборудования",
    );
    if (!emptyCheck.isValid) results.push(emptyCheck);

    // Проверка длины
    const lengthCheck = EquipmentValidation.checkNameLength(equipmentName);
    if (!lengthCheck.isValid) results.push(lengthCheck);

    // Проверка дубликатов
    const duplicateCheck = EquipmentValidation.checkDuplicateEquipment(
      equipmentName,
      parentId,
      allEquipment,
    );
    if (!duplicateCheck.isValid) results.push(duplicateCheck);

    return {
      isValid: results.length === 0,
      errors: results,
    };
  },

  // Комплексная валидация создания поставщика
  validateCreateSupplier: (supplierName, allSuppliers) => {
    const results = [];

    const emptyCheck = EquipmentValidation.checkEmptyField(
      supplierName,
      "Название поставщика",
    );
    if (!emptyCheck.isValid) results.push(emptyCheck);

    const lengthCheck = EquipmentValidation.checkNameLength(supplierName);
    if (!lengthCheck.isValid) results.push(lengthCheck);

    const duplicateCheck = EquipmentValidation.checkDuplicateSupplier(
      supplierName,
      allSuppliers,
    );
    if (!duplicateCheck.isValid) results.push(duplicateCheck);

    return {
      isValid: results.length === 0,
      errors: results,
    };
  },

  // Комплексная валидация создания неисправности
  validateCreateMalfunction: (malfunctionName, allMalfunctions) => {
    const results = [];

    const emptyCheck = EquipmentValidation.checkEmptyField(
      malfunctionName,
      "Название неисправности",
    );
    if (!emptyCheck.isValid) results.push(emptyCheck);

    const lengthCheck = EquipmentValidation.checkNameLength(malfunctionName);
    if (!lengthCheck.isValid) results.push(lengthCheck);

    const duplicateCheck = EquipmentValidation.checkDuplicateMalfunction(
      malfunctionName,
      allMalfunctions,
    );
    if (!duplicateCheck.isValid) results.push(duplicateCheck);

    return {
      isValid: results.length === 0,
      errors: results,
    };
  },
};
