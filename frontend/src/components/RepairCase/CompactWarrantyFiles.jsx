import React from "react";
import { useAuth } from "../../context/AuthContext";
import { BaseCompactFiles } from "./BaseCompactFiles";

export const CompactWarrantyFiles = (props) => {
  const { user } = useAuth();
  if (user?.restricted_access) return null;
  return <BaseCompactFiles {...props} category="warranty" />;
};
