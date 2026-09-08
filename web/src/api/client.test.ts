import { describe, expect, it } from "vitest";

import { ApiError, money, newIdempotencyKey } from "./client";

describe("money", () => {
  it("formats a decimal string without going through a float", () => {
    expect(money("2800.00")).toBe("₹2,800.00");
  });

  it("keeps paise that a float would lose", () => {
    expect(money("4453081.25")).toBe("₹44,53,081.25");
  });
});

describe("newIdempotencyKey", () => {
  it("is long enough for the API, which demands at least 8 characters", () => {
    expect(newIdempotencyKey().length).toBeGreaterThanOrEqual(8);
  });

  it("differs each call, so two separate payments are two payments", () => {
    expect(newIdempotencyKey()).not.toBe(newIdempotencyKey());
  });
});

describe("ApiError", () => {
  it("maps FastAPI 422 detail onto field names", () => {
    const e = new ApiError(422, [
      { type: "missing", loc: ["body", "amount"], msg: "Field required" },
    ]);
    expect(e.fields.amount).toBe("Field required");
  });

  it("carries a plain string detail through", () => {
    expect(new ApiError(403, "This role does not have permission: fees.invoice.read").detail).toContain(
      "does not have permission",
    );
  });
});
