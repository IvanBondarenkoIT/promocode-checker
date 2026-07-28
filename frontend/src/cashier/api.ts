import type { CashierCodeResponse, HeartbeatResponse } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

export type SystemHealthState = "connecting" | "ready" | "degraded" | "offline";

export type SystemHealth = {
  state: SystemHealthState;
  message: string;
  ready: boolean;
};

type HealthPayload = {
  status?: string;
  database?: string;
  schema?: string;
};

export function parseHealthPayload(payload: HealthPayload): SystemHealth {
  if (payload.database !== "ok") {
    return { state: "offline", message: "Database offline", ready: false };
  }
  if (payload.schema === "missing") {
    return { state: "degraded", message: "DB not initialized", ready: false };
  }
  if (payload.status === "ok" && payload.database === "ok" && payload.schema === "ok") {
    return { state: "ready", message: "Ready", ready: true };
  }
  return { state: "degraded", message: "System degraded", ready: false };
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    const text = await response.text();
    if (text) {
      try {
        const payload = JSON.parse(text) as { detail?: string };
        message = payload.detail ?? text;
      } catch {
        message = text;
      }
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export function checkPromocode(code: string, pointId: string): Promise<CashierCodeResponse> {
  return postJson<CashierCodeResponse>("/api/v1/cashier/check", {
    code,
    point_id: pointId,
  });
}

export function redeemPromocode(code: string, pointId: string): Promise<CashierCodeResponse> {
  return postJson<CashierCodeResponse>("/api/v1/cashier/redeem", {
    code,
    point_id: pointId,
  });
}

export function sendHeartbeat(pointId: string): Promise<HeartbeatResponse> {
  return postJson<HeartbeatResponse>("/api/v1/cashier/heartbeat", {
    point_id: pointId,
  });
}

export async function fetchSystemHealth(): Promise<SystemHealth> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) {
      return { state: "offline", message: "Offline", ready: false };
    }
    const payload = (await response.json()) as HealthPayload;
    return parseHealthPayload(payload);
  } catch {
    return { state: "offline", message: "Offline", ready: false };
  }
}
