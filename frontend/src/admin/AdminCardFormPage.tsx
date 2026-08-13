import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  CampaignSummary,
  PromocodeDefaults,
  createPromocode,
  deletePromocode,
  fetchPromocode,
  fetchPromocodeDefaults,
  patchPromocode,
} from "./api";
import { useAdminSession } from "./AdminContext";

function toDatetimeLocalValue(iso: string | null | undefined): string {
  if (!iso) {
    return "";
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function fromDatetimeLocalValue(value: string): string | undefined {
  if (!value.trim()) {
    return undefined;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return undefined;
  }
  return date.toISOString();
}

export function AdminCardFormPage() {
  const { cardId } = useParams();
  const isNew = !cardId || cardId === "new";
  const navigate = useNavigate();
  const { session } = useAdminSession();
  const isAdmin = session?.role === "admin";

  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
  const [campaignId, setCampaignId] = useState("");
  const [customerErpId, setCustomerErpId] = useState("");
  const [promocode, setPromocode] = useState("");
  const [customerCard, setCustomerCard] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [status, setStatus] = useState("ACTIVE");
  const [expiresAt, setExpiresAt] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [ttlDays, setTtlDays] = useState<number | null>(null);

  const title = useMemo(() => (isNew ? "Add customer card" : "Edit customer card"), [isNew]);

  useEffect(() => {
    if (!session) {
      return;
    }
    setLoading(true);
    setError(null);
    const load = async () => {
      const defaults: PromocodeDefaults = await fetchPromocodeDefaults(session.token);
      setCampaigns(defaults.campaigns);
      setTtlDays(defaults.promocode_ttl_days);
      if (isNew) {
        setCampaignId(defaults.default_campaign_id ?? "");
        setStatus(defaults.status || "ACTIVE");
        setExpiresAt(toDatetimeLocalValue(defaults.expires_at));
        setCustomerErpId("");
        setPromocode("");
        setCustomerCard("");
        setCustomerName("");
        setCustomerPhone("");
        return;
      }
      const detail = await fetchPromocode(session.token, cardId!);
      setCampaignId(detail.campaign_id ?? "");
      setCustomerErpId(detail.customer_erp_id);
      setPromocode(detail.promocode);
      setCustomerCard(detail.customer_card ?? "");
      setCustomerName(detail.customer_name ?? "");
      setCustomerPhone(detail.customer_phone ?? "");
      setStatus(detail.status);
      setExpiresAt(toDatetimeLocalValue(detail.expires_at));
    };
    load()
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load card"))
      .finally(() => setLoading(false));
  }, [session, cardId, isNew]);

  const onPromocodeBlur = () => {
    if (!customerCard.trim() && promocode.trim()) {
      setCustomerCard(promocode.trim());
    }
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!session || !isAdmin || !reason.trim()) {
      return;
    }
    setMessage(null);
    setError(null);
    const cardValue = customerCard.trim() || promocode.trim();
    const expiresIso = fromDatetimeLocalValue(expiresAt);
    try {
      if (isNew) {
        const created = await createPromocode(session.token, {
          customer_erp_id: customerErpId.trim(),
          promocode: promocode.trim(),
          customer_card: cardValue || null,
          customer_name: customerName.trim() || null,
          customer_phone: customerPhone.trim() || null,
          campaign_id: campaignId || null,
          status,
          expires_at: expiresIso,
          reason: reason.trim(),
        });
        setMessage("Created");
        navigate(`/admin/cards/${created.entity_id}`, { replace: true });
        return;
      }
      await patchPromocode(session.token, cardId!, {
        customer_erp_id: customerErpId.trim(),
        promocode: promocode.trim(),
        customer_card: cardValue || null,
        customer_name: customerName.trim() || null,
        customer_phone: customerPhone.trim() || null,
        campaign_id: campaignId || undefined,
        clear_campaign: !campaignId,
        status,
        expires_at: expiresIso,
        reason: reason.trim(),
      });
      setMessage("Saved");
      setReason("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  };

  const onDelete = async () => {
    if (!session || !isAdmin || isNew || !cardId) {
      return;
    }
    if (!reason.trim()) {
      setError("Reason is required to delete");
      return;
    }
    if (!window.confirm("Delete this customer card permanently?")) {
      return;
    }
    setError(null);
    try {
      await deletePromocode(session.token, cardId, reason.trim());
      navigate("/admin/cards", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  if (!session) {
    return null;
  }

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <div>
          <h1>{title}</h1>
          <p>{isNew ? "Defaults follow the active campaign kind" : `ID: ${cardId}`}</p>
        </div>
        <div className="admin-header-actions">
          <Link to="/admin/cards">Back to list</Link>
          <Link to="/admin/dashboard">Dashboard</Link>
        </div>
      </header>

      {error ? <p className="admin-error">{error}</p> : null}
      {message ? <p className="admin-ok">{message}</p> : null}
      {loading ? <p>Loading...</p> : null}

      {!loading ? (
        <form className="admin-card admin-card-wide" onSubmit={onSubmit} data-testid="admin-card-form">
          <label htmlFor="campaign">Campaign</label>
          <select
            id="campaign"
            data-testid="admin-card-campaign"
            value={campaignId}
            disabled={!isAdmin}
            onChange={(e) => setCampaignId(e.target.value)}
          >
            <option value="">No campaign</option>
            {campaigns.map((campaign) => (
              <option key={campaign.id ?? campaign.code} value={campaign.id ?? ""}>
                {campaign.code} ({campaign.kind}/{campaign.status})
              </option>
            ))}
          </select>

          <label htmlFor="erp">ERP customer ID</label>
          <input
            id="erp"
            data-testid="admin-card-erp"
            value={customerErpId}
            disabled={!isAdmin}
            onChange={(e) => setCustomerErpId(e.target.value)}
            required
          />

          <label htmlFor="promocode">Promocode (8–20 digits)</label>
          <input
            id="promocode"
            data-testid="admin-card-promocode"
            value={promocode}
            disabled={!isAdmin}
            onChange={(e) => setPromocode(e.target.value)}
            onBlur={onPromocodeBlur}
            required
          />

          <label htmlFor="card">Customer card</label>
          <input
            id="card"
            data-testid="admin-card-customer-card"
            value={customerCard}
            disabled={!isAdmin}
            onChange={(e) => setCustomerCard(e.target.value)}
            placeholder="Defaults to promocode"
          />

          <label htmlFor="name">Customer name</label>
          <input
            id="name"
            value={customerName}
            disabled={!isAdmin}
            onChange={(e) => setCustomerName(e.target.value)}
          />

          <label htmlFor="phone">Customer phone</label>
          <input
            id="phone"
            value={customerPhone}
            disabled={!isAdmin}
            onChange={(e) => setCustomerPhone(e.target.value)}
          />

          <label htmlFor="status">Status</label>
          <select
            id="status"
            data-testid="admin-card-status"
            value={status}
            disabled={!isAdmin}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="ACTIVE">ACTIVE</option>
            <option value="USED">USED</option>
          </select>

          <label htmlFor="expires">Expires at{ttlDays ? ` (TTL default ${ttlDays}d)` : ""}</label>
          <input
            id="expires"
            type="datetime-local"
            data-testid="admin-card-expires"
            value={expiresAt}
            disabled={!isAdmin}
            onChange={(e) => setExpiresAt(e.target.value)}
          />

          <label htmlFor="reason">Reason (required for save/delete)</label>
          <textarea
            id="reason"
            data-testid="admin-card-reason"
            value={reason}
            disabled={!isAdmin}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            required={isAdmin}
          />

          {isAdmin ? (
            <div className="admin-form-actions">
              <button type="submit" data-testid="admin-card-save">
                {isNew ? "Create with audit" : "Save with audit"}
              </button>
              {!isNew ? (
                <button
                  type="button"
                  className="admin-danger"
                  data-testid="admin-card-delete"
                  onClick={onDelete}
                >
                  Delete
                </button>
              ) : null}
            </div>
          ) : (
            <p className="admin-note">Viewer mode: read-only.</p>
          )}
        </form>
      ) : null}
    </div>
  );
}
