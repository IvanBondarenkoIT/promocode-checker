const TOKEN_KEY = "promocode_checker_admin_token";
const ROLE_KEY = "promocode_checker_admin_role";
const USER_KEY = "promocode_checker_admin_user";

export type AdminSession = {
  token: string;
  role: "admin" | "viewer";
  username: string;
};

export function loadSession(): AdminSession | null {
  const token = localStorage.getItem(TOKEN_KEY);
  const role = localStorage.getItem(ROLE_KEY);
  const username = localStorage.getItem(USER_KEY);
  if (!token || !role || !username) {
    return null;
  }
  if (role !== "admin" && role !== "viewer") {
    return null;
  }
  return { token, role, username };
}

export function saveSession(session: AdminSession): void {
  localStorage.setItem(TOKEN_KEY, session.token);
  localStorage.setItem(ROLE_KEY, session.role);
  localStorage.setItem(USER_KEY, session.username);
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(USER_KEY);
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function adminLogin(username: string, password: string): Promise<AdminSession> {
  const payload = await request<{ token: string; username: string; role: string }>(
    "/api/v1/admin/login",
    {
      method: "POST",
      body: JSON.stringify({ username, password }),
    },
  );
  return {
    token: payload.token,
    username: payload.username,
    role: payload.role as AdminSession["role"],
  };
}

export type DashboardStats = {
  promocodes_active: number;
  promocodes_used: number;
  promocodes_expired: number;
  scans_last_24h: number;
  auto_closes_total: number;
  fraud_open: number;
  telegram_sent_last_24h: number;
};

export async function fetchDashboard(token: string): Promise<DashboardStats> {
  return request<DashboardStats>("/api/v1/admin/dashboard", {}, token);
}

export type TableResponse = {
  table: string;
  total: number;
  limit: number;
  offset: number;
  rows: Record<string, unknown>[];
};

export async function fetchTable(
  token: string,
  table: string,
  offset = 0,
): Promise<TableResponse> {
  return request<TableResponse>(`/api/v1/admin/tables/${table}?limit=50&offset=${offset}`, {}, token);
}

export async function patchPromocode(
  token: string,
  promocodeId: string,
  body: { status?: string; expires_at?: string; reason: string },
): Promise<void> {
  await request(`/api/v1/admin/promocodes/${promocodeId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  }, token);
}

export async function patchFraudWarning(
  token: string,
  warningId: string,
  body: { status: string; reason: string },
): Promise<void> {
  await request(`/api/v1/admin/fraud-warnings/${warningId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  }, token);
}
