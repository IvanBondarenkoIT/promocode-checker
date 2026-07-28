import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AdminRoutes } from "./admin/AdminRoutes";
import { CashierApp } from "./cashier/CashierApp";
import "./styles/admin.css";
import "./styles/cashier.css";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CashierApp />} />
        <Route path="/admin/*" element={<AdminRoutes />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
