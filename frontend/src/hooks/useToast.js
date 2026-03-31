import { useState, useCallback } from 'react';

export const useToast = () => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((toast) => {
    const id = Date.now() + Math.random();
    const newToast = { ...toast, id };
    
    setToasts(prev => [...prev, newToast]);
    
    // Автоудаление через 6 секунд
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 6000);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const showError = useCallback((title, message) => {
    addToast({ type: 'error', title, message });
  }, [addToast]);

  const showSuccess = useCallback((title, message) => {
    addToast({ type: 'success', title, message });
  }, [addToast]);

  const showWarning = useCallback((title, message) => {
    addToast({ type: 'warning', title, message });
  }, [addToast]);

  const showInfo = useCallback((title, message) => {
    addToast({ type: 'info', title, message });
  }, [addToast]);

  return {
    toasts,
    addToast,
    removeToast,
    showError,
    showSuccess,
    showWarning,
    showInfo
  };
};
