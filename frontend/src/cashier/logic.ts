export const DEBOUNCE_LOCK_MS = 1500;

export function digitsOnly(value: string): string {
  return value.replace(/\D/g, "").slice(0, 8);
}

export function isCompleteCode(value: string): boolean {
  return /^\d{8}$/.test(value);
}

export type StatusTone = "idle" | "active" | "used" | "missing" | "error";

export function resultToTone(result: string | null): StatusTone {
  switch (result) {
    case "valid":
    case "redeemed":
      return "active";
    case "used":
    case "expired":
      return "used";
    case "not_found":
      return "missing";
    case "invalid_format":
      return "error";
    default:
      return "idle";
  }
}

export function resultLabel(result: string | null): string {
  switch (result) {
    case "valid":
      return "АКТИВЕН";
    case "redeemed":
      return "ПРИМЕНЁН";
    case "used":
      return "ИСПОЛЬЗОВАН";
    case "expired":
      return "ИСТЁК";
    case "not_found":
      return "НЕ НАЙДЕН";
    case "invalid_format":
      return "НЕВЕРНЫЙ ФОРМАТ";
    default:
      return "ГОТОВ К СКАНИРОВАНИЮ";
  }
}

export function isSuccessResult(result: string | null): boolean {
  return result === "valid" || result === "redeemed";
}
