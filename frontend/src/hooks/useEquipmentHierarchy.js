import { useState, useEffect, useMemo } from "react";

export const useEquipmentHierarchy = ({
  currentId,
  allEquipment = [],
  mode = "old",
  initialLevels = null,
  currentData,
  updateField,
  isEditing,
}) => {
  const [levels, setLevels] = useState({
    lvl0: null,
    lvl1: null,
    lvl2: null,
    lvl3: null,
    lvl4: null,
  });

  const labels = [
    "Тип оборудования",
    "Оборудование",
    "Компонент",
    "Обозначение",
    "Элемент",
  ];

  // АВТОМАТИЧЕСКОЕ КОЛ-ВО ЭЛЕМЕНТА (Lvl 4)
  useEffect(() => {
    if (isEditing && levels.lvl4) {
      const fieldName =
        mode === "old" ? "element_quantity" : "new_element_quantity";
      if (currentData?.[fieldName] == null) {
        updateField(fieldName, 1);
      }
    }
  }, [levels.lvl4, mode, isEditing, currentData, updateField]);

  // АВТОМАТИЧЕСКОЕ КОЛ-ВО КОМПОНЕНТА (Lvl 3)
  useEffect(() => {
    if (isEditing && levels.lvl3) {
      const fieldName =
        mode === "old" ? "component_quantity" : "new_component_quantity";
      if (currentData?.[fieldName] == null) {
        updateField(fieldName, 1);
      }
    }
  }, [levels.lvl3, mode, isEditing, currentData, updateField]);

  // ВЫЧИСЛЕНИЕ УРОВНЕЙ ОБОРУДОВАНИЯ
  const equipmentWithLevels = useMemo(() => {
    if (!allEquipment || allEquipment.length === 0) return [];
    if (allEquipment[0].calculatedLevel !== undefined) return allEquipment;

    const map = new Map(allEquipment.map((item) => [item.id, item]));
    return allEquipment.map((item) => {
      let depth = 0;
      let current = item;
      let visited = new Set();

      while (current && current.parent_id && depth < 10) {
        if (visited.has(current.id)) break;
        visited.add(current.id);
        const parent = map.get(current.parent_id);
        if (parent) {
          depth++;
          current = parent;
        } else break;
      }

      return { ...item, calculatedLevel: depth };
    });
  }, [allEquipment]);

  // --- УСТАНОВКА УРОВНЕЙ ПРИ ИЗМЕНЕНИИ currentId ---
  useEffect(() => {
    if (currentId && equipmentWithLevels.length > 0) {
      const newLevels = {
        lvl0: null,
        lvl1: null,
        lvl2: null,
        lvl3: null,
        lvl4: null,
      };

      let current = equipmentWithLevels.find((i) => i.id === Number(currentId));
      while (current) {
        if (current.calculatedLevel <= 4) {
          newLevels[`lvl${current.calculatedLevel}`] = current.id;
        }
        current = equipmentWithLevels.find((i) => i.id === current.parent_id);
      }

      setLevels(newLevels);
    } else if (initialLevels && currentId === undefined) {
      setLevels((prev) => ({ ...prev, ...initialLevels }));
    } else {
      setLevels({ lvl0: null, lvl1: null, lvl2: null, lvl3: null, lvl4: null });
    }
  }, [currentId, equipmentWithLevels, initialLevels]);

  // ОБРАБОТКА ВЫБОРА УРОВНЯ
  const handleLevelSelect = (levelIndex, selectedId, onSelect) => {
    const id = selectedId ? Number(selectedId) : null;
    const oldId = levels[`lvl${levelIndex}`];
    const newLevels = { ...levels };
    const sfx = mode === "old" ? "_old" : "_new";

    // СБРОС ПОЛЕЙ ПРИ ИЗМЕНЕНИИ
    if (oldId !== id) {
      if (levelIndex <= 2) {
        updateField(`component_serial_number${sfx}`, "");
        updateField(`component_manufacture_date${sfx}`, "");
        updateField(`element_serial_number${sfx}`, "");
        updateField(`element_manufacture_date${sfx}`, "");
        if (mode === "old") {
          updateField("component_quantity", 1);
          updateField("element_quantity", null);
        }
      }
      if (levelIndex === 3 && id === null) {
        updateField(`component_serial_number${sfx}`, "");
        updateField(`component_manufacture_date${sfx}`, "");
      }
      if (levelIndex === 4 && id === null) {
        updateField(`element_serial_number${sfx}`, "");
        updateField(`element_manufacture_date${sfx}`, "");
        if (mode === "old") updateField("element_quantity", null);
      }
    }

    // ОБНОВЛЕНИЕ ИЕРАРХИИ
    if (!id) {
      // Сброс всех дочерних уровней
      for (let i = levelIndex; i <= 4; i++) {
        newLevels[`lvl${i}`] = null;
        if (i === 3) {
          updateField(`component_serial_number${sfx}`, "");
          updateField(`component_manufacture_date${sfx}`, "");
        }
        if (i === 4) {
          updateField(`element_serial_number${sfx}`, "");
          updateField(`element_manufacture_date${sfx}`, "");
          if (mode === "old") updateField("element_quantity", null);
        }
      }
    } else {
      // Установка нового уровня и родительских
      newLevels[`lvl${levelIndex}`] = id;
      let current = equipmentWithLevels.find((i) => i.id === id);

      while (current && current.parent_id) {
        const parent = equipmentWithLevels.find(
          (i) => i.id === current.parent_id,
        );
        if (parent) {
          newLevels[`lvl${parent.calculatedLevel}`] = parent.id;
          current = parent;
        } else break;
      }

      // Сброс дочерних уровней
      for (let i = levelIndex + 1; i <= 4; i++) {
        newLevels[`lvl${i}`] = null;
        if (i === 4) {
          updateField(`element_serial_number${sfx}`, "");
          updateField(`element_manufacture_date${sfx}`, "");
          if (mode === "old") updateField("element_quantity", null);
        }
      }
    }

    setLevels(newLevels);

    // ОПРЕДЕЛЕНИЕ ПОСТАВЩИКА
    let detectedSupplierId = null;
    for (let i = 4; i >= 0; i--) {
      const idAtLevel = newLevels[`lvl${i}`];
      if (idAtLevel) {
        const item = equipmentWithLevels.find((obj) => obj.id === idAtLevel);
        if (item && item.supplier_id) {
          detectedSupplierId = item.supplier_id;
          break;
        }
      }
    }

    // ВЫЗОВ CALLBACK
    onSelect({
      component:
        newLevels.lvl3 || newLevels.lvl2 || newLevels.lvl1 || newLevels.lvl0,
      element: newLevels.lvl4,
      supplierId: detectedSupplierId,
      fullHierarchy: newLevels,
    });
  };

  // ФИЛЬТРАЦИЯ ОПЦИЙ ДЛЯ УРОВНЯ
  const getFilteredOptions = (levelIndex) => {
    let activeParentId = null;
    for (let i = levelIndex - 1; i >= 0; i--) {
      if (levels[`lvl${i}`]) {
        activeParentId = levels[`lvl${i}`];
        break;
      }
    }

    let filteredOptions = equipmentWithLevels.filter(
      (i) => i.calculatedLevel === levelIndex,
    );

    if (activeParentId) {
      filteredOptions = filteredOptions.filter((item) => {
        let current = item;
        let safety = 0;
        while (current && current.parent_id && safety < 10) {
          if (current.parent_id === activeParentId) return true;
          current = equipmentWithLevels.find(
            (obj) => obj.id === current.parent_id,
          );
          safety++;
        }
        return false;
      });
    }

    return filteredOptions;
  };

  // ОПРЕДЕЛЕНИЕ ВИДИМЫХ УРОВНЕЙ
  const getVisibleIndices = (filterStrategy) => {
    if (mode === "old") return [0, 1, 2, 3, 4];
    switch (filterStrategy) {
      case "LEVEL_1":
        return [1];
      case "LEVEL_3":
        return [3];
      case "LEVEL_4":
        return [4];
      default:
        return [];
    }
  };

  // АКТИВНЫЙ ID ДЛЯ НЕИСПРАВНОСТЕЙ
  const activeId =
    levels.lvl4 || levels.lvl3 || levels.lvl2 || levels.lvl1 || levels.lvl0;

  return {
    levels,
    labels,
    equipmentWithLevels,
    activeId,
    handleLevelSelect,
    getFilteredOptions,
    getVisibleIndices,
  };
};
