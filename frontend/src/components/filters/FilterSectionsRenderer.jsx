import React from "react";
import { FilterSection } from "../SidebarBlocks/index.jsx";
import {
  LocomotiveBlock,
  EquipmentBlock,
  RepairBlock,
  WarrantyBlock,
  SupplierBlock,
  StatusBlock,
} from "../SidebarBlocks";
import { filterSectionsConfig } from "./FilterSectionConfig";

export const FilterSectionsRenderer = ({
  openSections,
  toggleSection,
  getSectionCount,
  sectionThemes,
  filters,
  options,
  updateFilter,
  userOptions,
}) => {
  const componentMap = {
    LocomotiveBlock,
    EquipmentBlock,
    RepairBlock,
    WarrantyBlock,
    SupplierBlock,
    StatusBlock,
  };

  return filterSectionsConfig.map((sectionConfig) => {
    const { key, title, icon, component: componentName, keys } = sectionConfig;
    const Component = componentMap[componentName];

    const componentProps = {
      filters,
      options,
      updateFilter,
    };

    if (componentName === "StatusBlock") {
      componentProps.userOptions = userOptions;
    }

    return (
      <FilterSection
        key={key}
        title={title}
        icon={icon}
        isOpen={openSections[key]}
        onToggle={() => toggleSection(key)}
        activeCount={getSectionCount(keys)}
        colorTheme={sectionThemes[key]}
      >
        <Component {...componentProps} />
      </FilterSection>
    );
  });
};
