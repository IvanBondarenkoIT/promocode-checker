import { FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { adminLogin } from "./api";
import { useAdminSession } from "./AdminContext";

export function AdminLoginPage() {
  const navigate = useNavigate();
  const { session, setSession } = useAdminSession();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (session) {
    return <Navigate to="/admin/dashboard" replace />;
  }

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const next = await adminLogin(username, password);
      setSession(next);
      navigate("/admin/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="admin-shell">
      <form className="admin-card" onSubmit={onSubmit}>
        <h1>Admin login</h1>
        <label htmlFor="username">Username</label>
        <input
          id="username"
          data-testid="admin-username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <label htmlFor="password">Password</label>
        <input
          id="password"
          data-testid="admin-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error ? <p className="admin-error">{error}</p> : null}
        <button type="submit" disabled={busy} data-testid="admin-login-submit">
          {busy ? "..." : "Login"}
        </button>
      </form>
    </div>
  );
}
