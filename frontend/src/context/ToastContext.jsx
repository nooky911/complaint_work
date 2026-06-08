import React, { createContext, useContext, useState, useCallback } from "react";
import { ErrorToast } from "../components/Toast/ErrorToast";

const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((toast) => {
    const id = Date.now() + Math.random();
    const newToast = { ...toast, id };

    setToasts((prev) => [...prev, newToast]);

    // Автоудаление через 6 секунд
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 6000);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showError = useCallback(
    (title, message) => {
      addToast({ type: "error", title, message });
    },
    [addToast],
  );

  const showSuccess = useCallback(
    (title, message) => {
      addToast({ type: "success", title, message });
    },
    [addToast],
  );

  const showWarning = useCallback(
    (title, message) => {
      addToast({ type: "warning", title, message });
    },
    [addToast],
  );

  const showInfo = useCallback(
    (title, message) => {
      addToast({ type: "info", title, message });
    },
    [addToast],
  );

  return (
    <ToastContext.Provider
      value={{
        showError,
        showSuccess,
        showWarning,
        showInfo,
        addToast,
        removeToast,
      }}
    >
      {children}
      <div className="pointer-events-none fixed top-10 right-10 z-[100] flex flex-col gap-3">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <ErrorToast
              show={true}
              type={toast.type}
              title={toast.title}
              message={toast.message}
              onClose={() => removeToast(toast.id)}
              staticPosition={true}
            />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};
