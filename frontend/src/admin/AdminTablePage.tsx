import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { TableResponse, fetchTable, patchFraudWarning, patchPromocode } from "./api";
import { useAdminSession } from "./AdminContext";

export function AdminTablePage() {
  const { tableName = "promocodes" } = useParams();
  const { session } = useAdminSession();
  const [data, setData] = useState<TableResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string>("");
  const [status, setStatus] = useState("ACTIVE");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const reload = () => {
    if (!session) {
      return;
    }
    fetchTable(session.token, tableName)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load table"));
  };

  useEffect(() => {
    reload();
  }, [session, tableName]);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!session || session.role !== "admin" || !selectedId || !reason.trim()) {
      return;
    }
    setMessage(null);
    setError(null);
    try {
      if (tableName === "promocodes") {
        await patchPromocode(session.token, selectedId, { status, reason: reason.trim() });
      } else if (tableName === "fraud_warnings") {
        await patchFraudWarning(session.token, selectedId, { status, reason: reason.trim() });
      }
      setMessage("Saved");
      setReason("");
      reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  };

  const columns = data?.rows[0] ? Object.keys(data.rows[0]) : [];

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <div>
          <h1>{tableName}</h1>
          <p>{data ? `${data.total} rows` : "..."}</p>
        </div>
        <Link to="/admin/dashboard">Dashboard</Link>
      </header>

      {error ? <p className="admin-error">{error}</p> : null}
      {message ? <p className="admin-ok">{message}</p> : null}

      <div className="admin-table-wrap">
        <table className="admin-table" data-testid="admin-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(data?.rows ?? []).map((row) => (
              <tr
                key={String(row.id)}
                className={selectedId === String(row.id) ? "selected" : ""}
                onClick={() => setSelectedId(String(row.id))}
              >
                {columns.map((col) => (
                  <td key={col}>{String(row[col] ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {session?.role === "admin" && (tableName === "promocodes" || tableName === "fraud_warnings") ? (
        <form className="admin-card" onSubmit={onSubmit}>
          <h2>Edit selected row</h2>
          <p>ID: {selectedId || "—"}</p>
          <label htmlFor="status">Status</label>
          <select id="status" value={status} onChange={(e) => setStatus(e.target.value)}>
            {tableName === "promocodes" ? (
              <>
                <option value="ACTIVE">ACTIVE</option>
                <option value="USED">USED</option>
              </>
            ) : (
              <>
                <option value="OPEN">OPEN</option>
                <option value="REVIEWED">REVIEWED</option>
                <option value="DISMISSED">DISMISSED</option>
              </>
            )}
          </select>
          <label htmlFor="reason">Reason</label>
          <textarea
            id="reason"
            data-testid="admin-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
          />
          <button type="submit" data-testid="admin-save">
            Save with audit
          </button>
        </form>
      ) : (
        <p className="admin-note">Viewer mode: read-only.</p>
      )}
    </div>
  );
}
