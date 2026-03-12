import { useState, useRef, useEffect } from "react";
import { User, ChevronDown, KeyRound, LogOut } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import ulLogo from "../../assets/logo/ul-logo.svg";

export default function Header({ onChangePassword }) {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const clickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target))
        setIsOpen(false);
    };
    document.addEventListener("mousedown", clickOutside);
    return () => document.removeEventListener("mousedown", clickOutside);
  }, []);

  if (!user) return null;

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white py-1">
      <div className="grid w-full grid-cols-3 items-center px-8">
        <div className="text-[24px] font-bold">Справка ППР</div>

        <div className="flex justify-center">
          <img src={String(ulLogo)} alt="Logo" className="h-10" />
        </div>

        <div className="relative flex justify-end" ref={dropdownRef}>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-2 rounded-lg p-2 transition-colors hover:bg-gray-100"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600">
              <User size={18} />
            </div>
            <span className="text-sm font-medium text-gray-700">
              {user?.full_name || "Пользователь"}
            </span>
            <ChevronDown
              size={16}
              className={`text-gray-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
            />
          </button>

          {isOpen && (
            <div className="animate-in fade-in zoom-in absolute top-full right-0 z-50 mt-2 w-48 rounded-md border border-gray-100 bg-white py-1 shadow-lg duration-100">
              <button
                onClick={() => {
                  onChangePassword();
                  setIsOpen(false);
                }}
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                <KeyRound size={14} /> Сменить пароль
              </button>

              <div className="my-1 border-t border-gray-50"></div>

              <button
                onClick={logout}
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                <LogOut size={14} /> Выйти
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
