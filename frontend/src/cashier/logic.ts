export const PROMOCODE_MIN_LENGTH = 8;
export const PROMOCODE_MAX_LENGTH = 20;
/** Typical loyalty card length — auto-submit when reached. */
export const PROMOCODE_AUTO_SUBMIT_LENGTH = 13;

export const DEBOUNCE_LOCK_MS = 1500;

export function digitsOnly(value: string): string {
  return value.replace(/\D/g, "").slice(0, PROMOCODE_MAX_LENGTH);
}

export function isCompleteCode(value: string): boolean {
  return (
    /^\d+$/.test(value) &&
    value.length >= PROMOCODE_MIN_LENGTH &&
    value.length <= PROMOCODE_MAX_LENGTH
  );
}

export function shouldAutoSubmit(value: string): boolean {
  return /^\d+$/.test(value) && value.length === PROMOCODE_AUTO_SUBMIT_LENGTH;
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
    case "out_of_scope":
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
    case "out_of_scope":
      return "OTHER CAMPAIGN";
    default:
      return "READY TO SCAN";
  }
}

/** Plain-English what-to-do line under the status label. */
export function resultInstruction(result: string | null, isError = false): string {
  if (isError) {
    return "Something went wrong with the connection. Wait a moment and try again, or call support.";
  }
  switch (result) {
    case "valid":
      return "This code is good. Give the discount in the cash register, then press Apply discount here.";
    case "redeemed":
      return "Discount recorded. You can scan the next customer.";
    case "used":
      return "This code was already used. Do not give the discount again.";
    case "expired":
      return "This code is too old and no longer valid. Do not accept it.";
    case "not_found":
      return "We do not have this code. Check the barcode or ask a supervisor.";
    case "invalid_format":
      return "Codes must be 8–20 digits (customer card). Scan again or re-enter carefully.";
    case "out_of_scope":
      return "This code belongs to another campaign that is not running now. Do not give the discount; call a supervisor.";
    default:
      return "Scan the customer’s card barcode, or type it and press Enter.";
  }
}

export function isSuccessResult(result: string | null): boolean {
  return result === "valid" || result === "redeemed";
}
