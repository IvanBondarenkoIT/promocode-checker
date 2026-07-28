import { Navigate, Route, Routes } from "react-router-dom";

import { AdminProvider, useAdminSession } from "./AdminContext";
import { AdminDashboardPage } from "./AdminDashboardPage";
import { AdminLoginPage } from "./AdminLoginPage";
import { AdminTablePage } from "./AdminTablePage";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { session } = useAdminSession();
  if (!session) {
    return <Navigate to="/admin/login" replace />;
  }
  return <>{children}</>;
}

export function AdminRoutes() {
  return (
    <AdminProvider>
      <Routes>
        <Route path="login" element={<AdminLoginPage />} />
        <Route
          path="dashboard"
          element={
            <RequireAuth>
              <AdminDashboardPage />
            </RequireAuth>
          }
        />
        <Route
          path="tables/:tableName"
          element={
            <RequireAuth>
              <AdminTablePage />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/admin/dashboard" replace />} />
      </Routes>
    </AdminProvider>
  );
}
