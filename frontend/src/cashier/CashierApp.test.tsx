import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CashierApp } from "./CashierApp";

const checkPromocode = vi.fn();
const redeemPromocode = vi.fn();
const sendHeartbeat = vi.fn();
const fetchSystemHealth = vi.fn();

vi.mock("./api", () => ({
  checkPromocode: (...args: unknown[]) => checkPromocode(...args),
  redeemPromocode: (...args: unknown[]) => redeemPromocode(...args),
  sendHeartbeat: (...args: unknown[]) => sendHeartbeat(...args),
  fetchSystemHealth: (...args: unknown[]) => fetchSystemHealth(...args),
}));

vi.mock("./audio", () => ({
  playSuccessBeep: vi.fn(),
  playErrorBuzz: vi.fn(),
}));

describe("CashierApp", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/?point_id=shop_test");
    localStorage.clear();
    checkPromocode.mockReset();
    redeemPromocode.mockReset();
    sendHeartbeat.mockReset();
    fetchSystemHealth.mockReset();
    fetchSystemHealth.mockResolvedValue({
      state: "ready",
      message: "Ready",
      ready: true,
    });
    sendHeartbeat.mockResolvedValue({
      ok: true,
      point_id: "shop_test",
      server_time: new Date().toISOString(),
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows point_id and rejects non-digits", async () => {
    const user = userEvent.setup();
    render(<CashierApp />);

    expect(screen.getByTestId("point-id")).toHaveTextContent("shop_test");
    const input = screen.getByTestId("promocode-input");
    await user.type(input, "12ab34");
    expect(input).toHaveValue("1234");
  });

  it("auto-submits on 8 digits and enables redeem for valid", async () => {
    const user = userEvent.setup();
    checkPromocode.mockResolvedValue({
      result: "valid",
      code: "12345678",
      point_id: "shop_test",
      status: "ACTIVE",
      expires_at: null,
      redeemed_at: null,
      log_id: 1,
    });

    render(<CashierApp />);
    const input = screen.getByTestId("promocode-input");
    await user.type(input, "12345678");

    await waitFor(() => {
      expect(checkPromocode).toHaveBeenCalledWith("12345678", "shop_test");
    });
    expect(screen.getByTestId("status-panel")).toHaveTextContent("ACTIVE");
    expect(screen.getByTestId("redeem-button")).not.toBeDisabled();
  });

  it("locks input for 1.5s after check", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    checkPromocode.mockResolvedValue({
      result: "not_found",
      code: "87654321",
      point_id: "shop_test",
      status: null,
      expires_at: null,
      redeemed_at: null,
      log_id: 2,
    });

    render(<CashierApp />);
    const input = screen.getByTestId("promocode-input");
    await user.type(input, "87654321");

    await waitFor(() => expect(checkPromocode).toHaveBeenCalled());
    expect(input).toBeDisabled();
    expect(screen.getByTestId("lock-hint")).toBeInTheDocument();

    await vi.advanceTimersByTimeAsync(1500);
    await waitFor(() => expect(input).not.toBeDisabled());
  });
});
