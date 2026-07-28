import type { CashierCodeResponse, HeartbeatResponse } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
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

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) {
      return false;
    }
    const payload = (await response.json()) as { status?: string };
    return payload.status === "ok";
  } catch {
    return false;
  }
}
