const STORAGE_KEY = "promocode_checker_point_id";

export function resolvePointId(): string {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = (params.get("point_id") || params.get("point") || "").trim();
  if (fromQuery) {
    localStorage.setItem(STORAGE_KEY, fromQuery);
    return fromQuery;
  }

  const fromStorage = (localStorage.getItem(STORAGE_KEY) || "").trim();
  if (fromStorage) {
    return fromStorage;
  }

  return (import.meta.env.VITE_DEFAULT_POINT_ID || "shop_01").trim() || "shop_01";
}

export function heartbeatIntervalMs(): number {
  const raw = Number(import.meta.env.VITE_HEARTBEAT_SECONDS || "60");
  const seconds = Number.isFinite(raw) && raw > 0 ? raw : 60;
  return seconds * 1000;
}
