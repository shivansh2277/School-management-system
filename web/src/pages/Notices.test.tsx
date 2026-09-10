import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Notices } from "./Notices";

/**
 * The delete on this screen is the destructive one, and two things about it
 * regress silently:
 *
 *  - the reason the clerk typed must be what reaches the API. A hardcoded
 *    string would still delete the notice, still write an audit row, and turn
 *    the whole trail into a record of the UI's opinion rather than theirs;
 *  - the button must not be usable without `comms.notice.publish`.
 *
 * Neither is visible to `tsc`, and both look fine on screen.
 */
const held: string[] = [];
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({ can: (p: string) => held.includes(p) }),
}));

const del = vi.fn((_path: string, _query?: string) => Promise.resolve(undefined));
vi.mock("../api/client", () => ({
  api: {
    get: (path: string) =>
      Promise.resolve(
        path === "/admin/notices"
          ? [
              {
                id: 7,
                title: "Fete postponed",
                audience: "all",
                published_by: "Head",
                published_at: "2026-09-10T00:00:00Z",
              },
            ]
          : [],
      ),
    post: vi.fn(),
    del: (path: string, query?: string) => del(path, query),
  },
}));

function renderNotices() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <Notices />
    </QueryClientProvider>,
  );
}

describe("Notices", () => {
  beforeEach(() => {
    del.mockClear();
    held.length = 0;
  });

  it("sends the reason the clerk typed, not one of its own", async () => {
    held.push("comms.notice.publish");
    renderNotices();

    fireEvent.click(await screen.findByRole("button", { name: "Delete" }));
    // The dialog will not submit without one, so nothing has been deleted yet.
    fireEvent.click(screen.getByRole("button", { name: "Delete notice" }));
    expect(del).not.toHaveBeenCalled();

    fireEvent.change(screen.getByRole("textbox", { name: /reason/i }), {
      target: { value: "Published in error" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Delete notice" }));

    await waitFor(() => expect(del).toHaveBeenCalledTimes(1));
    expect(del).toHaveBeenCalledWith("/admin/notices/7", "?reason=Published%20in%20error");
  });

  it("disables both write controls for a role without the permission", async () => {
    renderNotices();
    expect(await screen.findByRole("button", { name: "Delete" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Publish" })).toBeDisabled();
  });
});
