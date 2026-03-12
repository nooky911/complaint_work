import { useState, useRef, useEffect } from "react";

import {
  formatToDB,
  DATE_MASK,
  normalizeDateForInput,
} from "../utils/formatters";
import { isValidDate } from "../utils/validators";

export const useDatePicker = (value, onChange) => {
  const inputRef = useRef(null);
  const [cursorPos, setCursorPos] = useState(null);

  useEffect(() => {
    if (cursorPos !== null && inputRef.current) {
      inputRef.current.setSelectionRange(cursorPos, cursorPos);
    }
  }, [cursorPos, value]);

  const handleKeyDown = (e) => {
    const isNumber = /^\d$/.test(e.key);
    const isControlKey = [
      "Backspace",
      "Delete",
      "Tab",
      "Escape",
      "Enter",
      "ArrowLeft",
      "ArrowRight",
      "Home",
      "End",
    ].includes(e.key);

    if (!isNumber && !isControlKey) {
      e.preventDefault();
    }
  };

  const handleTextChange = (e) => {
    const input = e.target;
    const newValue = input.value;
    const selectionStart = input.selectionStart;
    const displayValue = normalizeDateForInput(value);

    if (newValue === "") {
      onChange(DATE_MASK);
      setCursorPos(0);
      return;
    }

    let raw = displayValue.split("");

    if (newValue.length > 10) {
      const char = newValue[selectionStart - 1];
      let pos = selectionStart - 1;

      if (pos === 2 || pos === 5) pos++;

      if (pos < 10 && /\d/.test(char)) {
        raw[pos] = char;
        setCursorPos(pos + 1);
      } else {
        setCursorPos(selectionStart - 1);
      }
    } else {
      let pos = selectionStart;
      if (pos === 2 || pos === 5) pos--;
      if (pos >= 0) {
        raw[pos] = "_";
        setCursorPos(pos);
      }
    }

    const res = raw.join("");
    const digitsOnly = res.replace(/\D/g, "");

    if (digitsOnly.length === 8) {
      const year = parseInt(res.substring(6, 10), 10);

      if (year >= 2000) {
        onChange(formatToDB(res));
      } else {
        onChange(res);
      }
    } else {
      onChange(res);
    }
  };

  const displayValue = normalizeDateForInput(value);
  const hasAnyDigits = /\d/.test(displayValue);
  const hasError =
    hasAnyDigits && (displayValue.includes("_") || !isValidDate(displayValue));

  return {
    inputRef,
    cursorPos,
    setCursorPos,
    handleKeyDown,
    handleTextChange,
    displayValue,
    hasError,
  };
};
