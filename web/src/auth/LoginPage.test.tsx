import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginPage } from "./LoginPage";

const mockLogin = vi.fn();
let mockMe: any = null;

vi.mock("./AuthContext", () => ({
  useAuth: () => ({
    me: mockMe,
    login: mockLogin,
  }),
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockMe = null;
  });

  it("renders all quick demo roles including Chief Provost, Boys Warden, and Girls Warden", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: "Admin" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accounts" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Admissions" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reception" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Transport" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Librarian" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Chief Provost" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Boys Warden" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Girls Warden" })).toBeInTheDocument();
  });

  it("clicking Chief Provost populates provost login and password", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Chief Provost" }));

    const emailInput = screen.getByPlaceholderText("admin@sunrisepublic.edu") as HTMLInputElement;
    const passwordInput = screen.getByPlaceholderText("••••••••••••") as HTMLInputElement;

    expect(emailInput.value).toBe("provost@sunrisepublic.edu");
    expect(passwordInput.value).toBe("Admin@123");
  });

  it("clicking Boys Warden populates warden.boys login and password", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Boys Warden" }));

    const emailInput = screen.getByPlaceholderText("admin@sunrisepublic.edu") as HTMLInputElement;
    const passwordInput = screen.getByPlaceholderText("••••••••••••") as HTMLInputElement;

    expect(emailInput.value).toBe("warden.boys@sunrisepublic.edu");
    expect(passwordInput.value).toBe("Admin@123");
  });

  it("clicking Girls Warden populates warden.girls login and password", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Girls Warden" }));

    const emailInput = screen.getByPlaceholderText("admin@sunrisepublic.edu") as HTMLInputElement;
    const passwordInput = screen.getByPlaceholderText("••••••••••••") as HTMLInputElement;

    expect(emailInput.value).toBe("warden.girls@sunrisepublic.edu");
    expect(passwordInput.value).toBe("Admin@123");
  });
});
