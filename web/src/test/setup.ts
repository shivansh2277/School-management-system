import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

if (typeof window !== "undefined") {
  window.scrollTo = vi.fn();
  if (typeof window.HTMLElement !== "undefined" && !window.HTMLElement.prototype.scrollIntoView) {
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  }
}
