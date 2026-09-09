import { describe, expect, it } from "vitest";

import { ApiError, money, newIdempotencyKey } from "./client";

describe("money", () => {
  it("formats a decimal string without going through a float", () => {
    expect(money("2800.00")).toBe("₹2,800.00");
  });

  it("keeps paise that a float would lose", () => {
    // 900719925474099.15 has 17 significant digits, past the ~15-17 a JS
    // double can hold exactly: Number(v) rounds it to ...099.10. Verified by
    // temporarily restoring `Number(v).toLocaleString(...)` in money() and
    // rerunning this test - it produces ₹90,07,19,92,54,74,099.10 and fails.
    expect(money("900719925474099.15")).toBe("₹90,07,19,92,54,74,099.15");
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
