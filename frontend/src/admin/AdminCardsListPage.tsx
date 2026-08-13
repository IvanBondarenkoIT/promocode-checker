import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { CampaignKind, TableResponse, fetchTable } from "./api";
import { useAdminSession } from "./AdminContext";

const PAGE_SIZE = 50;

const LIST_COLUMNS = [
  "promocode",
  "status",
  "customer_erp_id",
  "customer_name",
  "campaign_code",
  "campaign_kind",
  "expires_at",
] as const;

export function AdminCardsListPage() {
  const { session } = useAdminSession();
  const [data, setData] = useState<TableResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
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

  useEffect(() => {
    if (!session) {
      return;
    }
    fetchTable(session.token, "promocodes", {
      offset,
      limit: PAGE_SIZE,
      ...appliedFilters,
    })
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load cards"));
  }, [session, offset, appliedFilters]);

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

  const total = data?.total ?? 0;
  const pageEnd = Math.min(offset + PAGE_SIZE, total);
  const isAdmin = session?.role === "admin";

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <div>
          <h1>Customer cards</h1>
          <p>{data ? `${total} cards` : "..."}</p>
        </div>
        <div className="admin-header-actions">
          {isAdmin ? (
            <Link to="/admin/cards/new" data-testid="admin-add-card">
              Add card
            </Link>
          ) : null}
          <Link to="/admin/dashboard">Dashboard</Link>
        </div>
      </header>

      {error ? <p className="admin-error">{error}</p> : null}

      <form className="admin-filters" onSubmit={applyFilters} data-testid="admin-cards-filters">
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
        <button type="submit">Apply</button>
      </form>

      <div className="admin-table-wrap">
        <table className="admin-table" data-testid="admin-cards-table">
          <thead>
            <tr>
              {LIST_COLUMNS.map((col) => (
                <th key={col}>{col}</th>
              ))}
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {(data?.rows ?? []).map((row) => {
              const id = String(row.id ?? "");
              return (
                <tr key={id}>
                  {LIST_COLUMNS.map((col) => (
                    <td key={col}>{String(row[col] ?? "")}</td>
                  ))}
                  <td>
                    <Link to={`/admin/cards/${id}`} data-testid={`admin-open-card-${id}`}>
                      Open
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="admin-pagination">
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

      {!isAdmin ? <p className="admin-note">Viewer mode: read-only.</p> : null}
    </div>
  );
}
