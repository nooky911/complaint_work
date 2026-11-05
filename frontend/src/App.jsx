import { lazy, Suspense, useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";

import { getHomeSection, rememberViewerSection } from "./utils/userSections";
import { useAuth } from "./context/AuthContext";
import Header from "./components/Layout/Header";
import ChangePasswordModal from "./components/Modals/ChangePasswordModal";

const TrainDashboard = lazy(() => import("./train/pages/TrainDashboard"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const LocoDashboard = lazy(() => import("./loco/pages/LocoDashboard"));
const EquipmentManagementPage = lazy(
  () => import("./pages/EquipmentManagementPage.jsx"),
);
const ProductPassportsPage = lazy(() => import("./pages/ProductPassportsPage"));
const OmegaStockPage = lazy(() => import("./pages/OmegaStockPage"));
const AdminUsersPage = lazy(() => import("./pages/AdminUsersPage"));

/** Запоминает открытый раздел просмотра без привязки роли к группе */
function ViewerSectionMemory({ user }) {
  const location = useLocation();
  useEffect(() => rememberViewerSection(user, location), [user, location]);
  return null;
}

export default function App() {
  const { isAuth, loading, user } = useAuth();
  const [isPassModalOpen, setIsPassModalOpen] = useState(false);

  if (loading)
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
      </div>
    );

  return (
    <Router>
      <ViewerSectionMemory user={user} />
      <Suspense
        fallback={
          <div className="flex h-screen items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
          </div>
        }
      >
        {!isAuth ? (
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        ) : (
          <div className="h-screen bg-gray-50">
            <Header onChangePassword={() => setIsPassModalOpen(true)} />

            <main className="flex h-[calc(100vh-50px)] flex-1 flex-col">
              {user?.restricted_access ? (
                <Routes>
                  <Route path="/dashboard" element={<LocoDashboard />} />
                  <Route
                    path="*"
                    element={<Navigate to={getHomeSection(user)} replace />}
                  />
                </Routes>
              ) : (
                <Routes>
                  <Route
                    path="/"
                    element={<Navigate to={getHomeSection(user)} replace />}
                  />
                  <Route path="/dashboard" element={<LocoDashboard />} />
                  <Route path="/train" element={<TrainDashboard />} />
                  <Route
                    path="/train/product-passports"
                    element={
                      <ProductPassportsPage key="train" direction="train" />
                    }
                  />
                  <Route
                    path="/train/equipment-management"
                    element={
                      <EquipmentManagementPage key="train" direction="train" />
                    }
                  />
                  <Route
                    path="/equipment-management"
                    element={<EquipmentManagementPage key="loco" />}
                  />
                  <Route
                    path="/product-passports"
                    element={<ProductPassportsPage />}
                  />
                  <Route path="/omega-stock" element={<OmegaStockPage />} />
                  <Route path="/admin/users" element={<AdminUsersPage />} />
                  <Route
                    path="/login"
                    element={<Navigate to={getHomeSection(user)} replace />}
                  />
                  <Route
                    path="*"
                    element={<Navigate to={getHomeSection(user)} replace />}
                  />
                </Routes>
              )}
            </main>

            <ChangePasswordModal
              isOpen={isPassModalOpen}
              onClose={() => setIsPassModalOpen(false)}
            />
          </div>
        )}
      </Suspense>
    </Router>
  );
}
