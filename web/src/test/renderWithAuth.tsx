import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

import type { Me } from "../auth/AuthContext";

/** A signed-in staff member with exactly the permissions and modules given. */
export function makeMe(permissions: string[], modules: string[], name = "Test Staff"): Me {
  return {
    user: { id: 1, role: "admin", full_name: name, login_id: "test@example.com" },
    permissions,
    roles: [],
    school_code: "SPS",
    school_name: "Sunrise Public School",
    academic_year: "2025-26",
    modules,
  };
}

/**
 * Render with a fixed `me`, bypassing the network.
 *
 * The real AuthProvider fetches /auth/me on mount; these tests are about what
 * the registry does with a given set of permissions, so the identity is
 * injected rather than mocked over HTTP.
 *
 * This wraps only QueryClientProvider and MemoryRouter - it does not include
 * AuthProvider. A component that reads useAuth() needs its caller to mock
 * "../auth/AuthContext" (see Shell.test.tsx): AuthProvider only produces a
 * populated `me` after a real network round trip, which is exactly what this
 * helper exists to avoid.
 */
export function renderWithAuth(ui: ReactElement, me: Me, route = "/") {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}
