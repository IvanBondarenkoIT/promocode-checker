import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  CampaignKind,
  TableResponse,
  fetchTable,
  patchFraudWarning,
} from "./api";
import { useAdminSession } from "./AdminContext";

const PAGE_SIZE = 50;
const FILTERABLE = new Set([
  "promocodes",
  "campaigns",
  "checker_logs",
  "fraud_warnings",
  "sale_observations",
]);

export function AdminTablePage() {
  const { tableName = "promocodes" } = useParams();
  const { session } = useAdminSession();
  const [data, setData] = useState<TableResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string>("");
  const [status, setStatus] = useState("OPEN");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const [offset, setOffset] = useState(0);
  const [campaignCode, setCampaignCode] = useState("");
  const [kind, setKind] = useState<CampaignKind | "">("");
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [appliedFilters, setAppliedFilters] = useState({
    campaignCode: "",
    kind: "" as CampaignKind | "",
    status: "",
    search: "",
  });

  const reload = () => {
    if (!session) {
      return;
    }
    fetchTable(session.token, tableName, {
      offset,
      limit: PAGE_SIZE,
      ...appliedFilters,
    })
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load table"));
  };

  useEffect(() => {
    reload();
  }, [session, tableName, offset, appliedFilters]);

  useEffect(() => {
    setOffset(0);
    setAppliedFilters({ campaignCode: "", kind: "", status: "", search: "" });
    setCampaignCode("");
    setKind("");
    setStatusFilter("");
    setSearch("");
    setSelectedId("");
  }, [tableName]);

  const applyFilters = (event: FormEvent) => {
    event.preventDefault();
    setOffset(0);
    setAppliedFilters({
      campaignCode: campaignCode.trim(),
      kind,
      status: statusFilter.trim(),
      search: search.trim(),
    });
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!session || session.role !== "admin" || !selectedId || !reason.trim()) {
      return;
    }
    if (tableName !== "fraud_warnings") {
      return;
    }
    setMessage(null);
    setError(null);
    try {
      await patchFraudWarning(session.token, selectedId, { status, reason: reason.trim() });
      setMessage("Saved");
      setReason("");
      reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  };

  const columns = data?.rows[0] ? Object.keys(data.rows[0]) : [];
  const total = data?.total ?? 0;
  const pageEnd = Math.min(offset + PAGE_SIZE, total);

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <div>
          <h1>{tableName}</h1>
          <p>{data ? `${total} rows` : "..."}</p>
        </div>
        <div className="admin-header-actions">
          {tableName === "promocodes" ? <Link to="/admin/cards">Customer cards UI</Link> : null}
          <Link to="/admin/dashboard">Dashboard</Link>
        </div>
      </header>

      {error ? <p className="admin-error">{error}</p> : null}
      {message ? <p className="admin-ok">{message}</p> : null}

      {tableName === "promocodes" ? (
        <p className="admin-note">
          Edit or add cards in the <Link to="/admin/cards">Customer cards</Link> forms.
        </p>
      ) : null}

      {FILTERABLE.has(tableName) ? (
        <form className="admin-filters" onSubmit={applyFilters} data-testid="admin-filters">
          {tableName === "promocodes" || tableName === "campaigns" ? (
            <>
              <input
                aria-label="Campaign code"
                placeholder="Campaign code"
                value={campaignCode}
                onChange={(e) => setCampaignCode(e.target.value)}
              />
              <select
                aria-label="Campaign kind"
                value={kind}
                onChange={(e) => setKind(e.target.value as CampaignKind | "")}
              >
                <option value="">All kinds</option>
                <option value="TEST">TEST</option>
                <option value="LIVE">LIVE</option>
              </select>
            </>
          ) : null}
          <input
            aria-label="Status filter"
            placeholder="Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          />
          <input
            aria-label="Search"
            placeholder="Search code or customer"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit" data-testid="admin-apply-filters">
            Apply
          </button>
        </form>
      ) : null}

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

      <div className="admin-pagination" data-testid="admin-pagination">
        <button
          type="button"
          disabled={offset === 0}
          onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
        >
          Previous
        </button>
        <span>
          {total === 0 ? "0" : `${offset + 1}-${pageEnd}`} of {total}
        </span>
        <button
          type="button"
          disabled={pageEnd >= total}
          onClick={() => setOffset(offset + PAGE_SIZE)}
        >
          Next
        </button>
      </div>

      {session?.role === "admin" && tableName === "fraud_warnings" ? (
        <form className="admin-card" onSubmit={onSubmit}>
          <h2>Edit selected row</h2>
          <p>ID: {selectedId || "—"}</p>
          <label htmlFor="status">Status</label>
          <select id="status" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="OPEN">OPEN</option>
            <option value="REVIEWED">REVIEWED</option>
            <option value="DISMISSED">DISMISSED</option>
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
      ) : session?.role !== "admin" ? (
        <p className="admin-note">Viewer mode: read-only.</p>
      ) : null}
    </div>
  );
}
