import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

import { AdminSession, clearSession, loadSession, saveSession } from "./api";

type AdminContextValue = {
  session: AdminSession | null;
  setSession: (session: AdminSession | null) => void;
  logout: () => void;
};

const AdminContext = createContext<AdminContextValue | null>(null);

export function AdminProvider({ children }: { children: ReactNode }) {
  const [session, setSessionState] = useState<AdminSession | null>(() => loadSession());

  const value = useMemo(
    () => ({
      session,
      setSession: (next: AdminSession | null) => {
        if (next) {
          saveSession(next);
        } else {
          clearSession();
        }
        setSessionState(next);
      },
      logout: () => {
        clearSession();
        setSessionState(null);
      },
    }),
    [session],
  );

  return <AdminContext.Provider value={value}>{children}</AdminContext.Provider>;
}

export function useAdminSession(): AdminContextValue {
  const ctx = useContext(AdminContext);
  if (!ctx) {
    throw new Error("AdminProvider missing");
  }
  return ctx;
}
