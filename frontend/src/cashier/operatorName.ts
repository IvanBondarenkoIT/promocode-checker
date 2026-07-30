const STORAGE_KEY = "promocode_checker_operator_name";

export function resolveOperatorName(): string {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = (params.get("username") || params.get("operator") || "").trim();
  if (fromQuery) {
    localStorage.setItem(STORAGE_KEY, fromQuery);
    return fromQuery;
  }

  return (localStorage.getItem(STORAGE_KEY) || "").trim();
}
