import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "../api/errors";
import { ConfirmDialog } from "./ui";

/**
 * services/audit.py refuses to commit a void, a status change or a delete
 * without a reason, so a dialog that can submit an empty one produces a 422
 * the clerk cannot interpret. That is what these pin.
 */
describe("ConfirmDialog", () => {
  it("refuses to submit until a reason is typed", () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        title="Void invoice"
        intent="Invoice INV-001 will be voided."
        confirmLabel="Void"
        onConfirm={onConfirm}
        onClose={vi.fn()}
      />,
    );
    const confirm = screen.getByRole("button", { name: "Void" });
    expect(confirm).toBeDisabled();
    confirm.click();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("treats whitespace as no reason at all", () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog title="Void invoice" intent="x" onConfirm={onConfirm} onClose={vi.fn()} />,
    );
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "   " } });
    expect(screen.getByRole("button", { name: "Confirm" })).toBeDisabled();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("hands back the reason the user typed, trimmed, and not a canned string", () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog title="Void invoice" intent="x" onConfirm={onConfirm} onClose={vi.fn()} />,
    );
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "  duplicate of INV-002  " },
    });
    screen.getByRole("button", { name: "Confirm" }).click();
    expect(onConfirm).toHaveBeenCalledWith("duplicate of INV-002");
  });

  it("surfaces a failure that names no field, so a 500 does not vanish", () => {
    render(
      <ConfirmDialog
        title="Void invoice"
        intent="x"
        error={new ApiError(500, "Ledger is closed for this period")}
        onConfirm={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    expect(screen.getByText("Ledger is closed for this period")).toBeInTheDocument();
  });
});
