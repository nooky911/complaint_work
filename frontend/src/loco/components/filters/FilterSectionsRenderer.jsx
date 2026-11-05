import { FilterSection } from "../SidebarBlocks/index";
import {
  LocomotiveBlock,
  EquipmentBlock,
  RepairBlock,
  WarrantyBlock,
  TtnBlock,
  SupplierBlock,
  StatusBlock,
} from "../SidebarBlocks/index";
import { BLOCK_TITLES } from "../../../constants/labels";
import { filterSectionsConfig } from "./FilterSectionConfig";

export const FilterSectionsRenderer = ({
  direction = "loco",
  restricted = false,
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
    TtnBlock,
    SupplierBlock,
    StatusBlock,
  };

  return filterSectionsConfig
    .filter(
      (section) =>
        !restricted || !["ttn", "suppliers", "status"].includes(section.key),
    )
    .map((sectionConfig) => {
      const {
        key,
        title,
        icon,
        component: componentName,
        keys,
      } = sectionConfig;
      const Component = componentMap[componentName];

      const componentProps = {
        direction,
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
          title={
            direction === "train" && key === "locomotive"
              ? BLOCK_TITLES.train_block
              : title
          }
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
