import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AdminLoginPage } from "./AdminLoginPage";

const adminLogin = vi.fn();
const setSession = vi.fn();

vi.mock("./api", () => ({
  adminLogin: (...args: unknown[]) => adminLogin(...args),
}));

vi.mock("./AdminContext", () => ({
  useAdminSession: () => ({ session: null, setSession }),
}));

describe("AdminLoginPage", () => {
  it("renders login form", () => {
    render(
      <MemoryRouter>
        <AdminLoginPage />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("admin-username")).toBeInTheDocument();
    expect(screen.getByTestId("admin-password")).toBeInTheDocument();
  });

  it("submits credentials", async () => {
    adminLogin.mockResolvedValue({ token: "t", role: "admin", username: "admin" });
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AdminLoginPage />
      </MemoryRouter>,
    );
    await user.type(screen.getByTestId("admin-username"), "admin");
    await user.type(screen.getByTestId("admin-password"), "secret");
    await user.click(screen.getByTestId("admin-login-submit"));
    expect(adminLogin).toHaveBeenCalledWith("admin", "secret");
  });
});
