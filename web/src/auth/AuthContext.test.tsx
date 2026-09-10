import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "./AuthContext";

vi.mock("../api/client", () => ({
  api: { get: vi.fn(() => Promise.resolve({})), post: vi.fn() },
  tokenStore: { get: () => null, getRefresh: () => null, set: vi.fn(), clear: vi.fn() },
}));

function LogoutButton() {
  const { logout } = useAuth();
  return <button onClick={logout}>Sign out</button>;
}

/**
 * The counter PC in a school office is shared and signing out so a colleague
 * can sign in is the normal way it is used, so what survives a logout is a
 * question about who can see whose data - not about tidiness.
 */
describe("signing out", () => {
  it("empties the query cache, so the next person does not read the last one's data", async () => {
    const qc = new QueryClient();
    qc.setQueryData(["classes"], [{ id: 1, class_label: "10-A" }]);
    expect(qc.getQueryData(["classes"])).toBeDefined();

    render(
      <QueryClientProvider client={qc}>
        <AuthProvider>
          <LogoutButton />
        </AuthProvider>
      </QueryClientProvider>,
    );

    screen.getByRole("button", { name: "Sign out" }).click();

    expect(qc.getQueryData(["classes"])).toBeUndefined();
  });
});
