import {
  Train,
  Package,
  Settings,
  FileText,
  Building2,
  ShieldCheck,
} from "lucide-react";
import { BLOCK_TITLES } from "../../constants/labels";
import { SECTIONS_KEYS } from "../../constants/filters";

export const filterSectionsConfig = [
  {
    key: "locomotive",
    title: BLOCK_TITLES.locomotive_block,
    icon: Train,
    component: "LocomotiveBlock",
    keys: SECTIONS_KEYS.locomotive,
  },
  {
    key: "equipment",
    title: BLOCK_TITLES.equipment_block,
    icon: Package,
    component: "EquipmentBlock",
    keys: SECTIONS_KEYS.equipment,
  },
  {
    key: "repair",
    title: BLOCK_TITLES.repair_block,
    icon: Settings,
    component: "RepairBlock",
    keys: SECTIONS_KEYS.repair,
  },
  {
    key: "documents",
    title: BLOCK_TITLES.documents,
    icon: FileText,
    component: "WarrantyBlock",
    keys: SECTIONS_KEYS.documents,
  },
  {
    key: "suppliers",
    title: "Поставщик оборудования",
    icon: Building2,
    component: "SupplierBlock",
    keys: SECTIONS_KEYS.suppliers,
  },
  {
    key: "status",
    title: BLOCK_TITLES.status_info,
    icon: ShieldCheck,
    component: "StatusBlock",
    keys: SECTIONS_KEYS.status,
  },
];
