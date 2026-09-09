import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { makeMe, renderWithAuth } from "./test/renderWithAuth";
import { App } from "./App";

/**
 * A fee collector holds fees.invoice.read but not admin.settings.read, the
 * permission the old "/" (the Dashboard's own route) required. Signing in
 * used to land such a caller on a permission-denied panel with no way back.
 */
const feeCollector = makeMe(
  ["students.profile.read", "fees.invoice.read", "fees.payment.collect"],
  ["students", "fees"],
  "Priya Counter",
);

const noScreens = makeMe([], [], "Nobody");

describe("the index route at /", () => {
  it("sends a fee-collector-shaped identity to a screen they can open, not the Dashboard", async () => {
    vi.resetModules();
    vi.doMock("./auth/AuthContext", () => ({
      useAuth: () => ({
        me: feeCollector,
        loading: false,
        login: vi.fn(),
        logout: vi.fn(),
        can: (p: string) => feeCollector.permissions.includes(p),
        hasModule: (c: string) => feeCollector.modules.includes(c),
      }),
    }));
    const { App: MockedApp } = await import("./App");
    renderWithAuth(<MockedApp />, feeCollector, "/");

    // Students is the first screen in the registry this identity can open.
    // The permission-denied panel (what "/" used to show) must not appear.
    expect(await screen.findByText("Add Student")).toBeInTheDocument();
    expect(screen.queryByText("You do not have permission")).not.toBeInTheDocument();
    vi.doUnmock("./auth/AuthContext");
  });

  it("shows a no-screens panel instead of looping when a caller can open nothing", async () => {
    vi.resetModules();
    vi.doMock("./auth/AuthContext", () => ({
      useAuth: () => ({
        me: noScreens,
        loading: false,
        login: vi.fn(),
        logout: vi.fn(),
        can: () => false,
        hasModule: () => false,
      }),
    }));
    const { App: MockedApp } = await import("./App");
    renderWithAuth(<MockedApp />, noScreens, "/");

    expect(await screen.findByText("No screens enabled")).toBeInTheDocument();
    vi.doUnmock("./auth/AuthContext");
  });
});

describe("an unregistered path", () => {
  it("renders a not-found panel inside the shell instead of a blank pane", async () => {
    vi.resetModules();
    vi.doMock("./auth/AuthContext", () => ({
      useAuth: () => ({
        me: feeCollector,
        loading: false,
        login: vi.fn(),
        logout: vi.fn(),
        can: (p: string) => feeCollector.permissions.includes(p),
        hasModule: (c: string) => feeCollector.modules.includes(c),
      }),
    }));
    const { App: MockedApp } = await import("./App");
    renderWithAuth(<MockedApp />, feeCollector, "/nowhere");

    expect(await screen.findByText("Page not found")).toBeInTheDocument();
    vi.doUnmock("./auth/AuthContext");
  });
});
