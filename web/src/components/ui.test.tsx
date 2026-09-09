import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApiError } from "../api/errors";
import { DataTable } from "./ui";

const columns = [{ key: "n", header: "Name", render: (r: { n: string }) => r.n }];

describe("DataTable error state", () => {
  it("shows a refused message for a 403, not the empty-table text", () => {
    render(
      <DataTable rows={[]} empty="No rows here." error={new ApiError(403, "nope")} columns={columns} />,
    );
    expect(screen.getByText(/refused/i)).toBeInTheDocument();
    expect(screen.queryByText("No rows here.")).not.toBeInTheDocument();
  });

  it("shows a not-available message for a 404", () => {
    render(
      <DataTable rows={[]} empty="No rows here." error={new ApiError(404, "nope")} columns={columns} />,
    );
    expect(screen.getByText(/not available/i)).toBeInTheDocument();
  });

  it("falls back to a generic failure message for anything else", () => {
    render(<DataTable rows={[]} empty="No rows here." error={new Error("boom")} columns={columns} />);
    expect(screen.getByText(/could not load/i)).toBeInTheDocument();
  });

  it("still shows the genuine empty state when there is no error", () => {
    render(<DataTable rows={[]} empty="No rows here." columns={columns} />);
    expect(screen.getByText("No rows here.")).toBeInTheDocument();
  });
});
