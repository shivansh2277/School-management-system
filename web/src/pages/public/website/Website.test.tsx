import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { PublicLayout } from "../../../components/public/PublicLayout";
import { AboutPage } from "./AboutPage";
import { AcademicsPage } from "./AcademicsPage";
import { AdmissionsPage } from "./AdmissionsPage";
import { FacilitiesPage } from "./FacilitiesPage";
import { HomePage } from "./HomePage";

describe("Public Website - Navigation & Header", () => {
  it("renders school branding and the Login to ERP link in navbar", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <PublicLayout>
          <div>Page Content</div>
        </PublicLayout>
      </MemoryRouter>
    );

    // School branding appears in both navbar and footer
    expect(screen.getAllByText("Sunrise School").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/CBSE Affiliation No\. 2130000/i).length).toBeGreaterThanOrEqual(1);

    // Nav links in navbar
    const nav = screen.getByRole("navigation");
    expect(within(nav).getByRole("link", { name: "Home" })).toHaveAttribute("href", "/");
    expect(within(nav).getByRole("link", { name: "About" })).toHaveAttribute("href", "/about");
    expect(within(nav).getByRole("link", { name: "Academics" })).toHaveAttribute("href", "/academics");
    expect(within(nav).getByRole("link", { name: "Admissions" })).toHaveAttribute("href", "/admissions");
    expect(within(nav).getByRole("link", { name: "Facilities" })).toHaveAttribute("href", "/facilities");

    // Login to ERP button
    const erpLinks = screen.getAllByRole("link", { name: /Login to ERP/i });
    expect(erpLinks.length).toBeGreaterThanOrEqual(1);
    expect(erpLinks[0]).toHaveAttribute("href", "/login");
  });

  it("toggles the mobile hamburger menu and displays mobile navigation", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <PublicLayout>
          <div>Page Content</div>
        </PublicLayout>
      </MemoryRouter>
    );

    const hamburgerBtn = screen.getByLabelText("Open menu");
    fireEvent.click(hamburgerBtn);

    // Drawer should show the full Login to ERP Portal link
    expect(screen.getByText("Login to ERP Portal")).toBeInTheDocument();
  });
});

describe("Public Website - Home Page", () => {
  it("renders hero section, statistics, previews, leadership, and ERP gateway CTA", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <HomePage />
      </MemoryRouter>
    );

    // Hero title & ethos
    expect(screen.getByText(/Nurturing Curious Minds/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Explore Our School" })).toHaveAttribute("href", "/about");
    expect(screen.getByRole("link", { name: /^Admissions/i })).toHaveAttribute("href", "/admissions");

    // Key statistics demo figures
    expect(screen.getByText("1,200+")).toBeInTheDocument();
    expect(screen.getByText("75+")).toBeInTheDocument();
    expect(screen.getByText("15+")).toBeInTheDocument();
    expect(screen.getByText("25+")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();

    // Leadership message
    expect(screen.getByText("Dr. Ananya Sengupta")).toBeInTheDocument();
    expect(screen.getByText(/Leadership Message/i)).toBeInTheDocument();

    // ERP Gateway CTA section
    expect(screen.getByText("Sunrise School ERP Gateway")).toBeInTheDocument();
    const staffErpBtn = screen.getByRole("link", { name: /Launch Staff ERP/i });
    expect(staffErpBtn).toHaveAttribute("href", "/login");
  });
});

describe("Public Website - About Page", () => {
  it("renders school heritage, vision, mission, and five core values", () => {
    render(
      <MemoryRouter initialEntries={["/about"]}>
        <AboutPage />
      </MemoryRouter>
    );

    expect(screen.getByText("About Sunrise School")).toBeInTheDocument();
    expect(screen.getByText(/A Legacy of Child-Centric Learning/i)).toBeInTheDocument();
    expect(screen.getByText(/Our Vision/i)).toBeInTheDocument();
    expect(screen.getByText(/Our Mission/i)).toBeInTheDocument();

    // Core values
    expect(screen.getByText(/Satya \(Integrity\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Karmanya \(Diligence\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Karuna \(Empathy\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Utkarsh \(Excellence\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Jigyasa \(Curiosity\)/i)).toBeInTheDocument();
  });
});

describe("Public Website - Academics Page", () => {
  it("renders wing structure, technology learning, and assessment approach", () => {
    render(
      <MemoryRouter initialEntries={["/academics"]}>
        <AcademicsPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Academics at Sunrise School")).toBeInTheDocument();
    expect(screen.getByText("Foundational Stage")).toBeInTheDocument();
    expect(screen.getByText("Preparatory & Middle Stage")).toBeInTheDocument();
    expect(screen.getByText("Secondary & Senior Secondary")).toBeInTheDocument();
    expect(screen.getByText("Technology-Enabled Learning")).toBeInTheDocument();
    expect(screen.getByText("CBSE Assessment Architecture")).toBeInTheDocument();
  });
});

describe("Public Website - Admissions Page", () => {
  it("renders admission process steps, age criteria table, and links to online apply", () => {
    render(
      <MemoryRouter initialEntries={["/admissions"]}>
        <AdmissionsPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Admissions at Sunrise School")).toBeInTheDocument();
    expect(screen.getByText("How to Secure Admission")).toBeInTheDocument();
    expect(screen.getByText("Registration")).toBeInTheDocument();
    expect(screen.getByText("Campus Interaction")).toBeInTheDocument();
    expect(screen.getByText("Verification")).toBeInTheDocument();
    expect(screen.getByText("Seat Offer")).toBeInTheDocument();
    expect(screen.getByText("Fee & Enrollment")).toBeInTheDocument();

    // Age criteria table
    expect(screen.getByText(/Age Criteria/i)).toBeInTheDocument();
    expect(screen.getByText("Nursery / Pre-School")).toBeInTheDocument();

    // Links to /apply
    const applyLinks = screen.getAllByRole("link", { name: /Fill Online Application Form/i });
    expect(applyLinks.length).toBeGreaterThanOrEqual(1);
    expect(applyLinks[0]).toHaveAttribute("href", "/apply");
  });
});

describe("Public Website - Facilities Page", () => {
  it("renders campus facilities cards with modern features", () => {
    render(
      <MemoryRouter initialEntries={["/facilities"]}>
        <FacilitiesPage />
      </MemoryRouter>
    );

    expect(screen.getByText("World-Class Campus Facilities")).toBeInTheDocument();
    expect(screen.getByText("Interactive Smart Classrooms")).toBeInTheDocument();
    expect(screen.getByText("Composite Science Laboratories")).toBeInTheDocument();
    expect(screen.getByText("Computer, AI & Robotics Hub")).toBeInTheDocument();
    expect(screen.getByText("Central Library & Media Center")).toBeInTheDocument();
    expect(screen.getByText("Sports Complex & Athletic Grounds")).toBeInTheDocument();
    expect(screen.getByText("GPS-Monitored Safe Transport")).toBeInTheDocument();
    expect(screen.getByText("Health & Medical Infirmary")).toBeInTheDocument();
  });
});
