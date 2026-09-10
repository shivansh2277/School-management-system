import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Can, ActionButton } from "./Can";

/**
 * A clerk who may collect a payment but may not void an invoice - the exact
 * split Contract 3 is about. Mocking AuthContext for the same reason
 * Shell.test.tsx does: the real provider only populates `me` after a round trip
 * to /auth/me, and this is a rendering test.
 */
const held = ["fees.payment.collect"];
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({ can: (p: string) => held.includes(p) }),
}));

describe("Can", () => {
  it("renders children for a permission the role holds", () => {
    render(<Can permission="fees.payment.collect">Take payment</Can>);
    expect(screen.getByText("Take payment")).toBeInTheDocument();
  });

  it("renders nothing for a permission the role lacks", () => {
    render(<Can permission="fees.invoice.void">Void invoice</Can>);
    expect(screen.queryByText("Void invoice")).not.toBeInTheDocument();
  });

  it("shows the fallback instead, when one is given", () => {
    render(
      <Can permission="fees.invoice.void" fallback={<span>Ask the accountant</span>}>
        Void invoice
      </Can>,
    );
    expect(screen.getByText("Ask the accountant")).toBeInTheDocument();
  });
});

describe("ActionButton", () => {
  it("is clickable for a permission the role holds", () => {
    const onClick = vi.fn();
    render(
      <ActionButton permission="fees.payment.collect" onClick={onClick}>
        Collect
      </ActionButton>,
    );
    const button = screen.getByRole("button", { name: "Collect" });
    expect(button).toBeEnabled();
    button.click();
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("disables itself and names the missing permission, rather than 403ing on click", () => {
    const onClick = vi.fn();
    render(
      <ActionButton permission="fees.invoice.void" onClick={onClick}>
        Void
      </ActionButton>,
    );
    const button = screen.getByRole("button", { name: "Void" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("title", "Your role does not hold fees.invoice.void");
    button.click();
    expect(onClick).not.toHaveBeenCalled();
  });
});
