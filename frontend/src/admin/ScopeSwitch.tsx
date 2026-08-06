import { useEffect, useState } from "react";

import { CampaignKind, ScopeResponse, fetchScope, updateScope } from "./api";
import { useAdminSession } from "./AdminContext";

type Props = {
  onChanged?: (kind: CampaignKind) => void;
};

/** Global data scope: which campaigns the cashier and reconcile actually serve. */
export function ScopeSwitch({ onChanged }: Props) {
  const { session } = useAdminSession();
  const [scope, setScope] = useState<ScopeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!session) {
      return;
    }
    fetchScope(session.token)
      .then(setScope)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load scope"));
  }, [session]);

  const switchTo = async (kind: CampaignKind) => {
    if (!session || session.role !== "admin" || !scope || scope.active_campaign_kind === kind) {
      return;
    }
    const reason = window.prompt(
      kind === "LIVE"
        ? "Switching to LIVE: real customer promocodes become active. Reason?"
        : "Switching to TEST: real promocodes stop being served. Reason?",
    );
    if (!reason || reason.trim().length < 3) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const next = await updateScope(session.token, kind, reason.trim());
      setScope(next);
      onChanged?.(next.active_campaign_kind);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Switch failed");
    } finally {
      setBusy(false);
    }
  };

  if (!scope) {
    return null;
  }

  const active = scope.active_campaign_kind;

  return (
    <section className={`admin-scope admin-scope-${active.toLowerCase()}`} data-testid="admin-scope">
      <div className="admin-scope-head">
        <span>Working data</span>
        <strong data-testid="admin-scope-active">{active}</strong>
      </div>

      <div className="admin-scope-actions">
        {(["TEST", "LIVE"] as CampaignKind[]).map((kind) => (
          <button
            key={kind}
            type="button"
            data-testid={`admin-scope-${kind.toLowerCase()}`}
            disabled={busy || active === kind || session?.role !== "admin"}
            onClick={() => switchTo(kind)}
          >
            {kind}
          </button>
        ))}
      </div>

      {error ? <p className="admin-error">{error}</p> : null}

      <table className="admin-table admin-scope-table">
        <thead>
          <tr>
            <th>Campaign</th>
            <th>Kind</th>
            <th>Status</th>
            <th>Issued</th>
            <th>Used</th>
          </tr>
        </thead>
        <tbody>
          {scope.campaigns.map((campaign) => (
            <tr key={campaign.code} className={campaign.kind === active ? "selected" : ""}>
              <td>{campaign.name}</td>
              <td>{campaign.kind}</td>
              <td>{campaign.status}</td>
              <td>{campaign.issued}</td>
              <td>{campaign.used}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
