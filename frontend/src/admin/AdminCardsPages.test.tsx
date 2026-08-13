import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminCardsListPage } from "./AdminCardsListPage";
import { AdminCardFormPage } from "./AdminCardFormPage";

const fetchTable = vi.fn();
const fetchPromocodeDefaults = vi.fn();
const fetchPromocode = vi.fn();

vi.mock("./api", () => ({
  fetchTable: (...args: unknown[]) => fetchTable(...args),
  fetchPromocodeDefaults: (...args: unknown[]) => fetchPromocodeDefaults(...args),
  fetchPromocode: (...args: unknown[]) => fetchPromocode(...args),
  createPromocode: vi.fn(),
  patchPromocode: vi.fn(),
  deletePromocode: vi.fn(),
}));

const sessionState = {
  session: { token: "t", role: "admin" as const, username: "admin" },
};

vi.mock("./AdminContext", () => ({
  useAdminSession: () => sessionState,
}));

describe("AdminCardsListPage", () => {
  beforeEach(() => {
    sessionState.session = { token: "t", role: "admin", username: "admin" };
    fetchTable.mockResolvedValue({
      table: "promocodes",
      total: 1,
      limit: 50,
      offset: 0,
      rows: [
        {
          id: "abc",
          promocode: "220021470",
          status: "ACTIVE",
          customer_erp_id: "21470",
          customer_name: "Shop",
          campaign_code: "TEST",
          campaign_kind: "TEST",
          expires_at: "2026-09-01T00:00:00+00:00",
        },
      ],
    });
  });

  it("shows Add card for admin and Open link", async () => {
    render(
      <MemoryRouter>
        <AdminCardsListPage />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("admin-add-card")).toBeInTheDocument();
    expect(await screen.findByTestId("admin-open-card-abc")).toBeInTheDocument();
  });

  it("hides Add card for viewer", async () => {
    sessionState.session = { token: "t", role: "viewer", username: "viewer" };
    render(
      <MemoryRouter>
        <AdminCardsListPage />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("admin-cards-table")).toBeInTheDocument();
    expect(screen.queryByTestId("admin-add-card")).not.toBeInTheDocument();
  });
});

describe("AdminCardFormPage", () => {
  beforeEach(() => {
    sessionState.session = { token: "t", role: "admin", username: "admin" };
    fetchPromocodeDefaults.mockResolvedValue({
      active_campaign_kind: "TEST",
      default_campaign_id: "camp-1",
      status: "ACTIVE",
      expires_at: "2026-09-01T00:00:00.000Z",
      promocode_ttl_days: 30,
      campaigns: [
        {
          id: "camp-1",
          code: "TEST_CAMP",
          name: "Test",
          kind: "TEST",
          status: "ACTIVE",
          issued: 0,
          used: 0,
        },
      ],
    });
  });

  it("renders create form with defaults", async () => {
    render(
      <MemoryRouter initialEntries={["/admin/cards/new"]}>
        <AdminCardFormPage />
      </MemoryRouter>,
    );
    expect(await screen.findByTestId("admin-card-form")).toBeInTheDocument();
    expect(screen.getByTestId("admin-card-save")).toBeInTheDocument();
    expect(screen.queryByTestId("admin-card-delete")).not.toBeInTheDocument();
  });
});
