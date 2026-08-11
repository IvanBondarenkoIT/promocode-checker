import { describe, expect, it } from "vitest";

import {
  digitsOnly,
  isCompleteCode,
  isSuccessResult,
  resultInstruction,
  resultLabel,
  resultToTone,
  shouldAutoSubmit,
} from "../cashier/logic";
import { resolvePointId } from "../cashier/pointId";

describe("cashier logic", () => {
  it("keeps only first 20 digits", () => {
    expect(digitsOnly("12ab34cd56789012345678999")).toBe("12345678901234567899");
  });

  it("validates complete 8-20 digit codes", () => {
    expect(isCompleteCode("12345678")).toBe(true);
    expect(isCompleteCode("2200000109743")).toBe(true);
    expect(isCompleteCode("1234567")).toBe(false);
    expect(isCompleteCode("1234567a")).toBe(false);
    expect(isCompleteCode("1".repeat(21))).toBe(false);
  });

  it("auto-submits only on 13-digit loyalty cards", () => {
    expect(shouldAutoSubmit("12345678")).toBe(false);
    expect(shouldAutoSubmit("2200000109743")).toBe(true);
    expect(shouldAutoSubmit("220000010974")).toBe(false);
  });

  it("maps status tones and labels", () => {
    expect(resultToTone("valid")).toBe("active");
    expect(resultToTone("used")).toBe("used");
    expect(resultToTone("not_found")).toBe("missing");
    expect(resultLabel("valid")).toBe("ACTIVE");
    expect(resultLabel("not_found")).toBe("NOT FOUND");
    expect(isSuccessResult("valid")).toBe(true);
    expect(isSuccessResult("used")).toBe(false);
  });

  it("provides plain-English instructions for every status", () => {
    expect(resultInstruction(null)).toMatch(/Scan the customer/i);
    expect(resultInstruction("valid")).toMatch(/Apply discount/i);
    expect(resultInstruction("redeemed")).toMatch(/next customer/i);
    expect(resultInstruction("used")).toMatch(/already used/i);
    expect(resultInstruction("expired")).toMatch(/no longer valid/i);
    expect(resultInstruction("not_found")).toMatch(/do not have this code/i);
    expect(resultInstruction("invalid_format")).toMatch(/8–20 digits/i);
    expect(resultInstruction(null, true)).toMatch(/connection/i);
  });
});

describe("point id resolution", () => {
  it("reads point_id from query and persists it", () => {
    window.history.pushState({}, "", "/?point_id=shop_99");
    localStorage.clear();
    expect(resolvePointId()).toBe("shop_99");
    expect(localStorage.getItem("promocode_checker_point_id")).toBe("shop_99");
  });

  it("falls back to stored point id", () => {
    window.history.pushState({}, "", "/");
    localStorage.setItem("promocode_checker_point_id", "shop_stored");
    expect(resolvePointId()).toBe("shop_stored");
  });
});
