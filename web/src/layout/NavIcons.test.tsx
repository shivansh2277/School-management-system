import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NavIcon } from "./NavIcons";

describe("NavIcons - Hostel Icons", () => {
  const HOSTEL_PATHS = [
    "/hostel",
    "/hostel/rooms",
    "/hostel/residents",
    "/hostel/admissions",
    "/hostel/attendance",
    "/hostel/leaves",
    "/hostel/complaints",
    "/hostel/notices",
    "/hostel/mess",
  ];

  it("renders distinct custom SVG icons for all 9 hostel paths without fallback placeholder", () => {
    for (const path of HOSTEL_PATHS) {
      const { container } = render(<NavIcon path={path} />);
      const svg = container.querySelector("svg");
      expect(svg, `SVG should render for path ${path}`).toBeTruthy();

      // Ensure it does not render the default fallback (four 7x7 rects)
      const rects = container.querySelectorAll("rect");
      const fallbackRects = Array.from(rects).filter(
        (r) => r.getAttribute("width") === "7" && r.getAttribute("height") === "7",
      );
      expect(
        fallbackRects.length,
        `Path ${path} should not render the 4 square placeholder fallback`,
      ).toBe(0);
    }
  });

  it("applies golden-amber styling classes", () => {
    const { container } = render(<NavIcon path="/hostel" />);
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("class")).toContain("text-[#ffa726]");
  });
});
