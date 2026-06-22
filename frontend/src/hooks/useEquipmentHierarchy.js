import { useState, useEffect, useMemo, useRef, useCallback } from "react";

export const useEquipmentHierarchy = ({
  currentId,
  allEquipment = [],
  mode = "old",
  initialLevels = null,
  currentData,
  updateField,
  isEditing,
  disableAutoFill = false,
}) => {
  const [levels, setLevels] = useState({
    lvl0: null,
    lvl1: null,
    lvl2: null,
    lvl3: null,
    lvl4: null,
  });

  const currentDataRef = useRef(currentData);
  useEffect(() => {
    currentDataRef.current = currentData;
  }, [currentData]);

  const labels = [
    "Тип оборудования",
    "Оборудование",
    "Компонент",
    "Обозначение",
    "Элемент",
  ];

  // ВЫЧИСЛЕНИЕ УРОВНЕЙ ОБОРУДОВАНИЯ
  const equipmentMap = useMemo(
    () => new Map(allEquipment.map((item) => [item.id, item])),
    [allEquipment],
  );

  const equipmentWithLevels = useMemo(() => {
    if (!allEquipment || allEquipment.length === 0) return [];
    if (allEquipment[0].calculatedLevel !== undefined) return allEquipment;

    return allEquipment.map((item) => {
      let depth = 0;
      let current = item;
      let visited = new Set();

      while (current && current.parent_id && depth < 10) {
        if (visited.has(current.id)) break;
        visited.add(current.id);
        const parent = equipmentMap.get(current.parent_id);
        if (parent) {
          depth++;
          current = parent;
        } else break;
      }

      return { ...item, calculatedLevel: depth };
    });
  }, [allEquipment, equipmentMap]);

  // АВТОМАТИЧЕСКОЕ КОЛ-ВО ЭЛЕМЕНТА (Lvl 4)
  useEffect(() => {
    if (isEditing && levels.lvl4 && !disableAutoFill) {
      const fieldName =
        mode === "old" ? "element_quantity" : "new_element_quantity";
      if (currentDataRef.current?.[fieldName] == null) {
        updateField(fieldName, 1);
      }
    }
  }, [levels.lvl4, mode, isEditing, updateField, disableAutoFill]);

  // АВТОМАТИЧЕСКОЕ КОЛ-ВО КОМПОНЕНТА (Lvl 3)
  useEffect(() => {
    if (isEditing && levels.lvl3 && !disableAutoFill) {
      const fieldName =
        mode === "old" ? "component_quantity" : "new_component_quantity";
      if (currentDataRef.current?.[fieldName] == null) {
        updateField(fieldName, 1);
      }
    }
  }, [levels.lvl3, mode, isEditing, updateField, disableAutoFill]);

  useEffect(() => {
    if (currentId && equipmentWithLevels.length > 0) {
      const isAlreadySet = Object.values(levels).includes(Number(currentId));
      if (isAlreadySet) return;

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
      setLevels((prev) => {
        const isAlreadyEmpty = Object.values(prev).every((v) => v === null);
        if (isAlreadyEmpty) return prev;
        return {
          lvl0: null,
          lvl1: null,
          lvl2: null,
          lvl3: null,
          lvl4: null,
        };
      });
    }
  }, [currentId, equipmentWithLevels, initialLevels]);

  // ОБРАБОТКА ВЫБОРА УРОВНЯ
  const handleLevelSelect = useCallback(
    (levelIndex, selectedId, onSelect) => {
      const id = selectedId ? Number(selectedId) : null;
      const sfx = mode === "old" ? "_old" : "_new";

      setLevels((prevLevels) => {
        const oldId = prevLevels[`lvl${levelIndex}`];
        if (oldId === id) return prevLevels;

        const nextLevels = { ...prevLevels };

        // Очистка текущего и дочерних уровней
        for (let i = levelIndex; i <= 4; i++) {
          nextLevels[`lvl${i}`] = i === levelIndex ? id : null;
        }

        // Восстановление родителей (если выбран новый ID)
        if (id) {
          let curr = equipmentMap.get(id);
          while (curr && curr.parent_id) {
            const parent = equipmentMap.get(curr.parent_id);
            if (parent) {
              const pLevel = equipmentWithLevels.find(
                (e) => e.id === parent.id,
              )?.calculatedLevel;
              if (pLevel !== undefined) nextLevels[`lvl${pLevel}`] = parent.id;
              curr = parent;
            } else break;
          }
        }

        // Расчет поставщика и вызов onSelect
        let detectedSupplierId = null;
        let highestLevel = -1;
        for (let i = 4; i >= 0; i--) {
          const idAtLvl = nextLevels[`lvl${i}`];
          if (idAtLvl) {
            if (highestLevel === -1) highestLevel = i;
            const item = equipmentMap.get(idAtLvl);
            if (item?.supplier_id && !detectedSupplierId) {
              detectedSupplierId = item.supplier_id;
            }
          }
        }

        setTimeout(() => {
          onSelect({
            component:
              nextLevels.lvl3 ||
              nextLevels.lvl2 ||
              nextLevels.lvl1 ||
              nextLevels.lvl0,
            element: nextLevels.lvl4,
            supplierId: detectedSupplierId,
            fullHierarchy: nextLevels,
            level: highestLevel,
          });
        }, 0);

        setTimeout(() => {
          for (let i = levelIndex; i <= 4; i++) {
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

          if (mode === "old" && levelIndex <= 3) {
            updateField("malfunction_id", null);
          }
        }, 0);

        return nextLevels;
      });
    },
    [mode, equipmentMap, equipmentWithLevels, updateField],
  );

  // ФИЛЬТРАЦИЯ ОПЦИЙ ДЛЯ УРОВНЯ
  const getFilteredOptions = useCallback(
    (levelIndex) => {
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
            current = equipmentMap.get(current.parent_id);
            safety++;
          }
          return false;
        });
      }

      return filteredOptions;
    },
    [equipmentWithLevels, equipmentMap, levels],
  );

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
