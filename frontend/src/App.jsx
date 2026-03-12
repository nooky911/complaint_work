import { useState } from "react";

import { useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import Header from "./components/Layout/Header";
import ChangePasswordModal from "./components/Modals/ChangePasswordModal";

export default function App() {
  const { isAuth, loading } = useAuth();
  const [isPassModalOpen, setIsPassModalOpen] = useState(false);

  if (loading)
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
      </div>
    );

  if (!isAuth) return <LoginPage />;

  return (
    <div className="h-screen bg-gray-50">
      <Header onChangePassword={() => setIsPassModalOpen(true)} />

      <main className="flex h-[calc(100vh-50px)] flex-1 flex-col">
        <DashboardPage />
      </main>

      <ChangePasswordModal
        isOpen={isPassModalOpen}
        onClose={() => setIsPassModalOpen(false)}
      />
    </div>
  );
}
