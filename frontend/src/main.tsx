import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { CashierApp } from "./cashier/CashierApp";
import "./styles/cashier.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <CashierApp />
  </StrictMode>,
);
