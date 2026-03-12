import { useState, useRef, useEffect } from "react";

export const useDropdown = (initialState = false, onCloseCallback) => {
  const [isOpen, setIsOpen] = useState(initialState);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
        if (onCloseCallback) onCloseCallback();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onCloseCallback]);

  const toggleDropdown = () => setIsOpen(!isOpen);
  const closeDropdown = () => {
    setIsOpen(false);
    if (onCloseCallback) onCloseCallback();
  };

  return {
    isOpen,
    setIsOpen,
    containerRef,
    toggleDropdown,
    closeDropdown,
  };
};
