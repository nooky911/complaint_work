import { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";

import { useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import EquipmentManagementPage from "./pages/EquipmentManagementPage";
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

  return (
    <Router>
      {!isAuth ? (
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      ) : (
        <div className="h-screen bg-gray-50">
          <Header onChangePassword={() => setIsPassModalOpen(true)} />

          <main className="flex h-[calc(100vh-50px)] flex-1 flex-col">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/equipment-management" element={<EquipmentManagementPage />} />
              <Route path="/login" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>

          <ChangePasswordModal
            isOpen={isPassModalOpen}
            onClose={() => setIsPassModalOpen(false)}
          />
        </div>
      )}
    </Router>
  );
}
