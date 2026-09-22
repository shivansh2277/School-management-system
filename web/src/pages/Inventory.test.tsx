import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SCREENS, visibleScreens } from "../screens";
import { Inventory } from "./Inventory";

// Mock the API client
vi.mock("../api/client", () => ({
  api: {
    get: vi.fn((url: string) => {
      if (url === "/admin/inventory/stats") {
        return Promise.resolve({
          low_stock_count: 18,
          pending_approvals_count: 7,
          discrepancies_count: 3,
          total_items: 32,
          critical_alerts: [
            {
              item_id: 1,
              title: "Printer Paper A4 (75 GSM)",
              subtitle: "Admin Store • 2 reams remaining",
              level: "critical",
              location: "Admin Store",
              category: "Stationery",
              current_quantity: 2,
              min_quantity: 10,
              unit: "reams",
            },
            {
              item_id: 2,
              title: "First-aid Supplies & Antiseptic Kits",
              subtitle: "Medical Room • Below minimum level",
              level: "critical",
              location: "Medical Room",
              category: "Medical Room",
              current_quantity: 1,
              min_quantity: 5,
              unit: "kits",
            },
            {
              item_id: 3,
              title: "Science Chemicals (Titration Reagents)",
              subtitle: "Science Lab • Reorder required",
              level: "critical",
              location: "Science Lab",
              category: "Science Lab",
              current_quantity: 2,
              min_quantity: 12,
              unit: "bottles",
            },
          ],
        });
      }
      if (url.startsWith("/admin/inventory/items")) {
        return Promise.resolve([
          {
            id: 1,
            name: "Printer Paper A4 (75 GSM)",
            category: "Stationery",
            location: "Admin Store",
            unit: "reams",
            current_quantity: 2,
            min_quantity: 10,
            unit_cost: "280.00",
            is_critical: true,
            has_discrepancy: false,
            is_low_stock: true,
          },
        ]);
      }
      if (url.startsWith("/admin/inventory/requests")) {
        return Promise.resolve([
          {
            id: 101,
            item_id: 1,
            item_name: "Printer Paper A4 (75 GSM)",
            category: "Stationery",
            location: "Admin Store",
            quantity_requested: 20,
            urgency: "critical",
            status: "pending",
            flag_type: "purchase",
            requested_by_id: 1,
            requested_by_name: "Administrator",
            reason: "Emergency reorder for question paper printing",
            created_at: new Date().toISOString(),
          },
        ]);
      }
      return Promise.resolve([]);
    }),
    post: vi.fn(() => Promise.resolve({})),
    patch: vi.fn(() => Promise.resolve({})),
  },
  ApiError: class ApiError extends Error {
    status: number;
    fields: Record<string, string>;
    constructor(status: number, message: string, fields = {}) {
      super(message);
      this.status = status;
      this.fields = fields;
    }
  },
}));

// Mock AuthContext
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    can: (p: string) => p.startsWith("inventory."),
    hasModule: (m: string) => m === "inventory",
    me: { school_name: "Sunrise Public School", user: { full_name: "Admin User" } },
  }),
}));

describe("Inventory Screen & Registry", () => {
  const can = (held: string[]) => (p: string) => held.includes(p);
  const hasModule = (on: string[]) => (c: string) => on.includes(c);

  it("registers Stock screen under Operations with inventory module gate", () => {
    const screenDef = SCREENS.find((s) => s.path === "/inventory");
    expect(screenDef).toBeDefined();
    expect(screenDef?.label).toBe("Stock");
    expect(screenDef?.group).toBe("Operations");
    expect(screenDef?.permissions).toEqual(["inventory.item.read"]);
    expect(screenDef?.modules).toEqual(["inventory"]);
  });

  it("shows Stock screen to roles with inventory.item.read when inventory module is enabled", () => {
    const visible = visibleScreens(
      can(["inventory.item.read"]),
      hasModule(["inventory"]),
    );
    expect(visible.map((s) => s.path)).toContain("/inventory");
  });

  it("hides Stock screen when inventory module is disabled", () => {
    const visible = visibleScreens(
      can(["inventory.item.read"]),
      hasModule(["transport", "fees"]), // inventory omitted
    );
    expect(visible.map((s) => s.path)).not.toContain("/inventory");
  });

  it("renders page heading and highlights with 3 StatCards", async () => {
    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={qc}>
        <Inventory />
      </QueryClientProvider>,
    );

    // Verify clean page heading without subtitle paragraph
    expect(screen.getByRole("heading", { level: 1, name: /Stock & Inventory/i })).toBeDefined();

    // Verify StatCards
    expect(screen.getByText("Low-stock items")).toBeDefined();
    expect(screen.getByText("Require review or reorder")).toBeDefined();

    expect(screen.getByText("Pending approvals")).toBeDefined();
    expect(screen.getByText("Purchase and issue requests")).toBeDefined();

    expect(screen.getByText("Stock discrepancies")).toBeDefined();
    expect(screen.getByText("Awaiting investigation")).toBeDefined();

    // Verify Critical stock alerts section
    expect(await screen.findByText("Critical stock alerts")).toBeDefined();
    expect(screen.getByText("Admin Store • 2 reams remaining")).toBeDefined();
    expect(screen.getByText("Medical Room • Below minimum level")).toBeDefined();
    expect(screen.getByText("Science Lab • Reorder required")).toBeDefined();
  });
});
