import { useState } from "react";
import { X, Eye, EyeOff } from "lucide-react";
import api from "../../api/api";

export default function ChangePasswordModal({ isOpen, onClose }) {
  const [form, setForm] = useState({ old_password: "", new_password: "" });

  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);

  const [error, setError] = useState("");

  if (!isOpen) return null;

  // Функция закрытия со сбросом всех полей
  const handleClose = () => {
    setForm({ old_password: "", new_password: "" });
    setError("");
    setShowOld(false);
    setShowNew(false);
    onClose();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (form.new_password.length < 8) {
      setError("Новый пароль должен быть не менее 8 символов");
      return;
    }

    try {
      await api.post("/users/me/password", form);
      handleClose();
    } catch (err) {
      const errorData = err.response?.data?.detail;

      if (typeof errorData === "string") {
        setError(errorData);
      } else if (Array.isArray(errorData)) {
        setError("Ошибка валидации: проверьте корректность данных");
      } else {
        setError("Не удалось изменить пароль");
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="animate-in fade-in zoom-in w-full max-w-md rounded-xl bg-white p-6 shadow-2xl duration-200">
        {/* Заголовок */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Смена пароля</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 transition-colors hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Старый пароль */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              Старый пароль
            </label>
            <div className="relative">
              <input
                required
                type={showOld ? "text" : "password"}
                className="w-full rounded-lg border border-gray-300 p-2.5 pr-10 transition-all outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                value={form.old_password}
                onChange={(e) =>
                  setForm({ ...form, old_password: e.target.value })
                }
              />
              <button
                type="button"
                onClick={() => setShowOld(!showOld)}
                className="absolute top-1/2 right-3 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showOld ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {/* Новый пароль */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              Новый пароль
            </label>
            <div className="relative">
              <input
                required
                type={showNew ? "text" : "password"}
                className="w-full rounded-lg border border-gray-300 p-2.5 pr-10 transition-all outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                value={form.new_password}
                onChange={(e) =>
                  setForm({ ...form, new_password: e.target.value })
                }
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                className="absolute top-1/2 right-3 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showNew ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {/* Блок ошибки */}
          {error && (
            <div className="rounded-lg border border-red-100 bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          {/* Кнопки действий */}
          <div className="mt-8 flex gap-3">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 rounded-lg border border-gray-300 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700"
            >
              Сохранить
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
