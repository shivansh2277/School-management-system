import { fireEvent, screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { makeMe, renderWithAuth } from "../test/renderWithAuth";
import { Shell } from "./Shell";

/**
 * Shell reads useAuth() directly (not through props), and the real
 * AuthProvider only produces a populated `me` after a network round trip to
 * /auth/me. Rather than wire a fetch mock for a component test that is about
 * rendering, not networking, mock the AuthContext module so useAuth() returns
 * a fixed value - the same trade the brief offers, taken on the "mock the
 * hook" side because it is the smaller, more direct diff here.
 */
const me = makeMe(
  ["students.profile.read", "fees.invoice.read", "fees.payment.collect"],
  [
    "students",
    "attendance",
    "examinations",
    "fees",
    "homework",
    "communication",
    "admission",
    "timetable",
    "hr",
    "transport",
    "reports",
  ],
  "Priya Counter",
);

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    me,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    can: (permission: string) => me.permissions.includes(permission),
    hasModule: (code: string) => me.modules.includes(code),
  }),
}));

describe("Shell", () => {
  it("renders only the sidebar links a fee collector's permissions and modules allow", () => {
    renderWithAuth(
      <Routes>
        <Route path="/" element={<Shell />} />
      </Routes>,
      me,
    );

    expect(screen.getByText("Students")).toBeInTheDocument();
    expect(screen.getByText("Fees")).toBeInTheDocument();
    expect(screen.queryByText("Staff")).not.toBeInTheDocument();
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();
    expect(screen.queryByText("Attendance")).not.toBeInTheDocument();
  });

  it("shows the school name and academic year from Me, not a hardcoded string", () => {
    renderWithAuth(
      <Routes>
        <Route path="/" element={<Shell />} />
      </Routes>,
      me,
    );

    expect(screen.getByText(/Sunrise Public School/)).toBeInTheDocument();
    expect(screen.getByText(/2025-26/)).toBeInTheDocument();
  });
});

/**
 * The sidebar toggle.
 *
 * The behaviour worth pinning is not that a class changes, it is that the
 * hidden sidebar stops being reachable by keyboard and that the button which
 * brings it back is still on screen. A collapse that only sets width to zero
 * looks right and leaves a clerk tabbing through a menu they cannot see.
 */
describe("Shell sidebar toggle", () => {
  const renderShell = () =>
    renderWithAuth(
      <Routes>
        <Route path="/" element={<Shell />} />
      </Routes>,
      me,
    );

  it("starts open, and the button says what it will do", () => {
    renderShell();
    const button = screen.getByRole("button", { name: "Hide navigation" });
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(button).toHaveAttribute("aria-controls", "app-sidebar");
  });

  it("hides the sidebar, and hides it from the keyboard too", () => {
    renderShell();
    fireEvent.click(screen.getByRole("button", { name: "Hide navigation" }));

    const sidebar = document.getElementById("app-sidebar");
    expect(sidebar?.className).toContain("w-0");
    // visibility:hidden, not merely zero width - this is the assertion that
    // fails if someone "simplifies" the collapse to a width change.
    expect(sidebar?.className).toContain("invisible");
  });

  it("keeps the button reachable once the sidebar is gone, and reopens", () => {
    renderShell();
    fireEvent.click(screen.getByRole("button", { name: "Hide navigation" }));

    const reopen = screen.getByRole("button", { name: "Show navigation" });
    expect(reopen).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(reopen);
    const sidebar = document.getElementById("app-sidebar");
    expect(sidebar?.className).toContain("w-60");
    expect(sidebar?.className).not.toContain("invisible");
    expect(screen.getByText("Students")).toBeInTheDocument();
  });
});
