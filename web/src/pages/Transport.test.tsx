import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Transport } from "./Transport";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn((url: string) => {
      if (url === "/admin/transport/routes") {
        return Promise.resolve([
          {
            id: 1,
            code: "R1",
            name: "Gomti Nagar Express",
            status: "active",
            distance_km: 14.5,
            vehicle: "UP32AB1234",
            capacity: 40,
            taken: 28,
            free: 12,
            stops: [
              {
                id: 101,
                sequence: 1,
                name: "Vibhuti Khand",
                address: "Vibhuti Khand, Gomti Nagar, Lucknow",
                landmark: "Fun Republic Mall",
                pickup_time: "06:40:00",
                drop_time: "14:25:00",
                latitude: 26.8722,
                longitude: 80.9994,
              },
            ],
          },
        ]);
      }
      if (url === "/admin/transport/vehicles") {
        return Promise.resolve([
          {
            id: 1,
            registration_no: "UP32AB1234",
            make_model: "Tata Starbus 40",
            capacity: 40,
            ownership: "owned",
            status: "active",
            gps_device_id: "GPS-UP32-001",
          },
        ]);
      }
      if (url === "/admin/transport/expiring") {
        return Promise.resolve([]);
      }
      if (url === "/admin/transport/slabs") {
        return Promise.resolve([
          { id: 1, name: "0-5 km", monthly_amount: 800, is_active: true },
        ]);
      }
      if (url === "/admin/transport/requests") {
        return Promise.resolve([]);
      }
      return Promise.resolve([]);
    }),
    post: vi.fn(() => Promise.resolve({})),
    patch: vi.fn(() => Promise.resolve({})),
    put: vi.fn(() => Promise.resolve({})),
    del: vi.fn(() => Promise.resolve({})),
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

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    can: (p: string) => p.startsWith("transport."),
    hasModule: (m: string) => m === "transport",
    me: { school_name: "Sunrise Public School", user: { full_name: "Transport In-Charge" } },
  }),
}));

describe("Transport Desk Screen — Plan 1 & Plan 2 Upgrade", () => {
  const renderScreen = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return render(
      <QueryClientProvider client={queryClient}>
        <Transport />
      </QueryClientProvider>,
    );
  };

  it("renders page heading, stat cards, and action desk buttons", async () => {
    renderScreen();

    expect(await screen.findByText("Transport & Fleet Management Desk")).toBeInTheDocument();
    expect(screen.getByText("Routes running")).toBeInTheDocument();
    expect(screen.getByText("Children riding")).toBeInTheDocument();
    expect(screen.getByText("Fleet capacity")).toBeInTheDocument();
    expect(screen.getByText("Papers lapsed")).toBeInTheDocument();

    // Verify Action buttons
    expect(screen.getByText(/Student Allocation Desk/i)).toBeInTheDocument();
    expect(screen.getByText("Distance Fee Slabs")).toBeInTheDocument();
    expect(screen.getByText("+ Add Vehicle")).toBeInTheDocument();
    expect(screen.getAllByText("+ New Route").length).toBeGreaterThan(0);
  });

  it("renders configured routes and fleet vehicles with GPS device ID", async () => {
    renderScreen();

    expect(await screen.findByText("Gomti Nagar Express")).toBeInTheDocument();
    expect(screen.getByText("R1")).toBeInTheDocument();
    expect(screen.getAllByText("UP32AB1234").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("GPS-UP32-001")).toBeInTheDocument();

    // Verify desk action buttons on the route row
    expect(screen.getByTitle("Interactive Route Map")).toBeInTheDocument();
    expect(screen.getByTitle("Print A4 Daily Manifest & Roster")).toBeInTheDocument();
    expect(screen.getByText("Crew")).toBeInTheDocument();
    expect(screen.getAllByText("Stops").length).toBeGreaterThanOrEqual(2);
  });
});
