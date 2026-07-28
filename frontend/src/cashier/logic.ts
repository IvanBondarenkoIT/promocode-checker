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
      return "ACTIVE";
    case "redeemed":
      return "APPLIED";
    case "used":
      return "USED";
    case "expired":
      return "EXPIRED";
    case "not_found":
      return "NOT FOUND";
    case "invalid_format":
      return "INVALID FORMAT";
    default:
      return "READY TO SCAN";
  }
}

export function isSuccessResult(result: string | null): boolean {
  return result === "valid" || result === "redeemed";
}
