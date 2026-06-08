import { useState, useEffect, useMemo } from "react";
import { useDropdown } from "./useDropdown";
import { useSearchFilter } from "./useSearchFilter";
import { sortOptionsBySelection } from "../utils/formatters";

export const useSearchableSelect = (options, value, onChange) => {
  const [searchTerm, setSearchTerm] = useState("");
  const { isOpen, setIsOpen, containerRef } = useDropdown();

  const selectedOption = options.find((opt) => opt.id === value);

  useEffect(() => {
    setSearchTerm(
      isOpen ? searchTerm : selectedOption ? selectedOption.name : "",
    );
  }, [isOpen, selectedOption, searchTerm]);

  const toggleDropdown = () => {
    if (isOpen) {
      setIsOpen(false);
    } else {
      setIsOpen(true);
      setSearchTerm("");
    }
  };

  const filteredOptions = useSearchFilter(options, searchTerm);

  const sortedOptions = useMemo(() => {
    return sortOptionsBySelection(filteredOptions, value);
  }, [filteredOptions, value]);

  const handleSelect = (id, name) => {
    onChange(id, name);
    setIsOpen(false);
  };

  const handleClear = () => {
    onChange(null, "");
    setIsOpen(false);
  };

  return {
    isOpen,
    setIsOpen,
    containerRef,
    searchTerm,
    setSearchTerm,
    selectedOption,
    filteredOptions: sortedOptions,
    toggleDropdown,
    handleSelect,
    handleClear,
  };
};
