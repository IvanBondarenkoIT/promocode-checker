import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { DashboardStats, fetchDashboard } from "./api";
import { useAdminSession } from "./AdminContext";
import { ScopeSwitch } from "./ScopeSwitch";

const TABLES = [
  "promocodes",
  "campaigns",
  "checker_logs",
  "fraud_warnings",
  "sale_observations",
  "admin_audit_logs",
  "telegram_notification_logs",
];

export function AdminDashboardPage() {
  const navigate = useNavigate();
  const { session, logout } = useAdminSession();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!session) {
      return;
    }
    fetchDashboard(session.token)
      .then(setStats)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load dashboard"));
  }, [session, reloadKey]);

  if (!session) {
    return null;
  }

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <div>
          <h1>Dashboard</h1>
          <p>
            {session.username} ({session.role})
          </p>
        </div>
        <div className="admin-header-actions">
          <Link to="/admin/tables/promocodes">Browse tables</Link>
          <button
            type="button"
            onClick={() => {
              logout();
              navigate("/admin/login");
            }}
          >
            Logout
          </button>
        </div>
      </header>

      {error ? <p className="admin-error">{error}</p> : null}

      <ScopeSwitch onChanged={() => setReloadKey((value) => value + 1)} />

      {stats ? (
        <div className="admin-grid" data-testid="admin-dashboard-grid">
          <div className="admin-stat">
            <span>Enforcement</span>
            <strong>
              {(stats.enforcement_mode || "monitor") === "enforce" ? "Working" : "Monitor"}
            </strong>
          </div>
          <div className="admin-stat">
            <span>Min coffee kg</span>
            <strong>{stats.promo_min_coffee_kg ?? 2}</strong>
          </div>
          <div className="admin-stat">
            <span>Active ({stats.active_campaign_kind})</span>
            <strong>{stats.promocodes_active}</strong>
          </div>
          <div className="admin-stat">
            <span>Used</span>
            <strong>{stats.promocodes_used}</strong>
          </div>
          <div className="admin-stat">
            <span>Expired</span>
            <strong>{stats.promocodes_expired}</strong>
          </div>
          <div className="admin-stat">
            <span>Scans 24h</span>
            <strong>{stats.scans_last_24h}</strong>
          </div>
          <div className="admin-stat">
            <span>Auto-closes</span>
            <strong>{stats.auto_closes_total}</strong>
          </div>
          <div className="admin-stat">
            <span>Sales seen 24h</span>
            <strong>
              {stats.sale_observations_24h ?? 0} / {stats.sale_qualified_24h ?? 0}
            </strong>
          </div>
          <div className="admin-stat">
            <span>Fraud open</span>
            <strong>{stats.fraud_open}</strong>
          </div>
          <div className="admin-stat">
            <span>Telegram 24h</span>
            <strong>{stats.telegram_sent_last_24h}</strong>
          </div>
        </div>
      ) : (
        <p>Loading...</p>
      )}

      <nav className="admin-nav">
        {TABLES.map((table) => (
          <Link key={table} to={`/admin/tables/${table}`}>
            {table}
          </Link>
        ))}
      </nav>
    </div>
  );
}
