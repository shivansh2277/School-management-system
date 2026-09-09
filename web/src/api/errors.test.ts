import { describe, expect, it } from "vitest";

import { ApiError, errorText } from "./errors";

describe("errorText", () => {
  it("reads the field reason off an ApiError's .detail, not the generic .message", () => {
    const e = new ApiError(422, [{ type: "missing", loc: ["body", "amount"], msg: "Field required" }]);
    expect(e.message).toBe("Request failed with 422");
    expect(errorText(e)).toBe("Field required");
  });

  it("falls back to .message for a plain Error", () => {
    expect(errorText(new Error("network down"))).toBe("network down");
  });
});
