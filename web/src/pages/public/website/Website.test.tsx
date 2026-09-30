import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { PublicLayout } from "../../../components/public/PublicLayout";
import { AboutPage } from "./AboutPage";
import { AcademicsPage } from "./AcademicsPage";
import { AdmissionsPage } from "./AdmissionsPage";
import { AnnouncementsPage } from "./AnnouncementsPage";
import { ContactPage } from "./ContactPage";
import { EventsPage } from "./EventsPage";
import { FacilitiesPage } from "./FacilitiesPage";
import { GalleryPage } from "./GalleryPage";
import { HomePage } from "./HomePage";
import { PublicDisclosurePage } from "./PublicDisclosurePage";
import { ResourcesPage } from "./ResourcesPage";
import { SchoolLifePage } from "./SchoolLifePage";

function renderWithClient(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("Public Website - Navigation & Header", () => {
  it("renders school branding, 9 primary institutional navigation links, ERP Login CTA, and persistent side Admission Enquiry CTA", () => {
    const { container } = render(
      <MemoryRouter initialEntries={["/"]}>
        <PublicLayout>
          <div>Page Content</div>
        </PublicLayout>
      </MemoryRouter>
    );

    // Desktop top utility bar is removed completely:
    const header = container.querySelector("header");
    expect(header).toBeInTheDocument();
    expect(within(header!).queryByText("Admissions Guide")).not.toBeInTheDocument();
    expect(within(header!).queryByText(/Academic Session 2026–27/i)).not.toBeInTheDocument();

    // School branding appears in navbar
    expect(screen.getAllByText("Sunrise School").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Gomti Nagar • Lucknow/i).length).toBeGreaterThanOrEqual(1);

    // 9 Institutional Navigation links in desktop navbar (Contact and Gallery removed)
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    expect(within(nav).getByRole("link", { name: "Home" })).toHaveAttribute("href", "/");
    expect(within(nav).getByRole("link", { name: "About" })).toHaveAttribute("href", "/about");
    expect(within(nav).getByRole("link", { name: "Academics" })).toHaveAttribute("href", "/academics");
    expect(within(nav).getByRole("link", { name: "Admissions" })).toHaveAttribute("href", "/admissions");
    expect(within(nav).getByRole("link", { name: "Campus & Facilities" })).toHaveAttribute("href", "/facilities");
    expect(within(nav).getByRole("link", { name: "School Life" })).toHaveAttribute("href", "/school-life");
    expect(within(nav).getByRole("link", { name: "Events" })).toHaveAttribute("href", "/events");
    expect(within(nav).getByRole("link", { name: "Public Disclosure" })).toHaveAttribute("href", "/public-disclosure");
    expect(within(nav).getByRole("link", { name: "Resources" })).toHaveAttribute("href", "/resources");

    // Contact and Gallery are REMOVED from primary navbar
    expect(within(nav).queryByRole("link", { name: "Contact" })).not.toBeInTheDocument();
    expect(within(nav).queryByRole("link", { name: "Gallery" })).not.toBeInTheDocument();

    // Right-side CTA in header is now "ERP Login →" linking to existing ERP login route
    const erpLoginLinks = within(header!).getAllByRole("link", { name: /ERP Login/i });
    expect(erpLoginLinks.length).toBeGreaterThanOrEqual(1);
    expect(erpLoginLinks[0]).toHaveAttribute("href", "/login");

    // Persistent Admission Enquiry side CTA is present in PublicLayout
    expect(screen.getByTestId("admission-side-cta-desktop")).toBeInTheDocument();
    expect(screen.getByTestId("admission-side-cta-mobile")).toBeInTheDocument();

    // Global Announcement Strip is present directly below navbar
    expect(screen.getByText("Latest Announcements")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /View All/i })).toHaveAttribute("href", "/announcements");
  });

  it("toggles the mobile hamburger menu and displays mobile navigation drawer with accessible phone dialer and ERP login link", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <PublicLayout>
          <div>Page Content</div>
        </PublicLayout>
      </MemoryRouter>
    );

    const hamburgerBtn = screen.getByLabelText("Toggle Navigation Menu");
    fireEvent.click(hamburgerBtn);

    // Drawer should show Apply Online and ERP Login
    expect(screen.getByText(/Apply Online Portal/i)).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /ERP Login/i }).length).toBeGreaterThanOrEqual(1);

    // Mobile phone desk action link with real tel: href
    const deskPhoneLinks = screen.getAllByRole("link", { name: /Call Admissions Desk/i });
    expect(deskPhoneLinks.length).toBeGreaterThanOrEqual(1);
    expect(deskPhoneLinks[0]).toHaveAttribute("href", "tel:+915222990000");
  });
});

describe("Public Website - Home Page", () => {
  it("renders hero section, 4 Sunrise School feature cards, Principal welcome, quote card, and stats", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <HomePage />
      </MemoryRouter>
    );

    // Hero title & ethos
    expect(screen.getByText(/Nurturing Curious Minds/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Explore Our School/i })).toHaveAttribute("href", "/about");
    expect(screen.getAllByRole("button", { name: /Admission Enquiry/i }).length).toBeGreaterThanOrEqual(1);

    // Four Sunrise School feature cards with photos
    expect(screen.getByText("Academic Excellence")).toBeInTheDocument();
    expect(screen.getByText("World-Class Facilities")).toBeInTheDocument();
    expect(screen.getByText("Supportive Community")).toBeInTheDocument();
    expect(screen.getByText("Beyond the Classroom")).toBeInTheDocument();

    // Principal Welcome & Quote Card
    expect(screen.getByText("Dr. Meera Sharma")).toBeInTheDocument();
    expect(screen.getByText("Welcome to Sunrise School")).toBeInTheDocument();
    expect(screen.getByText(/The purpose of education is to prepare the child for life, not just for exams/i)).toBeInTheDocument();

    // Key statistics demo figures
    expect(screen.getByText("1,200+")).toBeInTheDocument();
    expect(screen.getByText("75+")).toBeInTheDocument();
    expect(screen.getByText("15+")).toBeInTheDocument();
    expect(screen.getByText("25+")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });
});

describe("Public Website - About Page", () => {
  it("renders school heritage, founder section, founder quote, milestones timeline, 7-C philosophy, and core values", () => {
    render(
      <MemoryRouter initialEntries={["/about"]}>
        <AboutPage />
      </MemoryRouter>
    );

    expect(screen.getByText("About Sunrise School")).toBeInTheDocument();
    expect(screen.getByText(/A Legacy of Child-Centric Academic Excellence/i)).toBeInTheDocument();

    // Founder Section & Quote
    expect(screen.getByText("Dr. Anand Mohan Shukla")).toBeInTheDocument();
    expect(screen.getByText("Founder & Chairman, Board of Trustees")).toBeInTheDocument();
    expect(screen.getByText(/The true purpose of education is not merely to prepare a child for examinations/i)).toBeInTheDocument();

    // Institutional Milestones Timeline
    expect(screen.getByText("Institutional Milestones Timeline")).toBeInTheDocument();
    expect(screen.getByText("Foundation Stone Laid")).toBeInTheDocument();
    expect(screen.getByText("High School CBSE Affiliation")).toBeInTheDocument();
    expect(screen.getByText("Senior Secondary Accreditation")).toBeInTheDocument();

    // 7-C Educational Philosophy
    expect(screen.getByText("The 7-C Educational Philosophy")).toBeInTheDocument();
    expect(screen.getByText("Curiosity")).toBeInTheDocument();
    expect(screen.getByText("Critical Thinking")).toBeInTheDocument();
    expect(screen.getByText("Character")).toBeInTheDocument();
    expect(screen.getByText("Creativity")).toBeInTheDocument();
    expect(screen.getByText("Collaboration")).toBeInTheDocument();
    expect(screen.getByText("Communication")).toBeInTheDocument();
    expect(screen.getByText("Confidence")).toBeInTheDocument();

    // Core values
    expect(screen.getByText("Core Institutional Values")).toBeInTheDocument();
    expect(screen.getByText("Integrity")).toBeInTheDocument();
    expect(screen.getByText("Excellence")).toBeInTheDocument();
    expect(screen.getByText("Inclusivity")).toBeInTheDocument();
    expect(screen.getByText("Empathy")).toBeInTheDocument();
  });
});

describe("Public Website - Academics Page", () => {
  it("renders NEP stages, Senior Secondary streams, and syllabus download links", () => {
    render(
      <MemoryRouter initialEntries={["/academics"]}>
        <AcademicsPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Academics at Sunrise School")).toBeInTheDocument();
    expect(screen.getByText(/Foundational Stage \(Ages 3–8\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Preparatory & Middle Stages \(Ages 8–14\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Secondary & Senior Secondary \(Ages 14–18\)/i)).toBeInTheDocument();

    // Senior Secondary streams
    expect(screen.getByText("PCM / PCB Specialization")).toBeInTheDocument();
    expect(screen.getByText("Commerce & Finance")).toBeInTheDocument();
    expect(screen.getByText("Liberal Arts & Social Sciences")).toBeInTheDocument();

    // Downloads
    expect(screen.getByRole("link", { name: /Download Syllabus Overview/i })).toHaveAttribute("href", "/documents/syllabus-overview.pdf");
    expect(screen.getByRole("link", { name: /Academic Calendar 2026–27/i })).toHaveAttribute("href", "/documents/academic-calendar.pdf");
  });
});

describe("Public Website - Admissions Page", () => {
  it("renders admission process steps, eligibility checklist, FAQs, and link to apply portal", () => {
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

    // Link directly to the real admission portal
    const applyButtons = screen.getAllByRole("link", { name: /Start New Application/i });
    expect(applyButtons[0]).toHaveAttribute("href", "/apply");
  });
});

describe("Public Website - Facilities Page", () => {
  it("renders campus infrastructure cards with safety specifications", () => {
    render(
      <MemoryRouter initialEntries={["/facilities"]}>
        <FacilitiesPage />
      </MemoryRouter>
    );

    expect(screen.getByText("World-Class Campus Facilities")).toBeInTheDocument();
    expect(screen.getByText("Campus Infrastructure")).toBeInTheDocument();
    expect(screen.getByText("Interactive Smart Classrooms")).toBeInTheDocument();
    expect(screen.getByText("Composite Science Laboratories")).toBeInTheDocument();
    expect(screen.getByText("Computer, AI & Robotics Hub")).toBeInTheDocument();
    expect(screen.getByText("Central Library & Media Center")).toBeInTheDocument();
    expect(screen.getByText("Sports Complex & Athletic Grounds")).toBeInTheDocument();
  });
});

describe("Public Website - School Life Page", () => {
  it("renders co-curricular activities, house system, and merged photo gallery at bottom", () => {
    render(
      <MemoryRouter initialEntries={["/school-life"]}>
        <SchoolLifePage />
      </MemoryRouter>
    );

    expect(screen.getByText("School Life & Campus Gallery")).toBeInTheDocument();
    expect(screen.getByText("The Four Houses of Sunrise")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Agni House" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Prithvi House" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Vayu House" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Jal House" })).toBeInTheDocument();

    // Merged Photo Gallery at bottom of School Life
    expect(screen.getByText("Sunrise School Campus Photo Gallery")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All Photos" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Campus & Architecture" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Classrooms & Labs" })).toBeInTheDocument();
  });
});

describe("Public Website - Events Page", () => {
  it("renders events schedule with category tabs and upcoming highlights", () => {
    render(
      <MemoryRouter initialEntries={["/events"]}>
        <EventsPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Events & Academic Calendar")).toBeInTheDocument();
    expect(screen.getByText("Upcoming School Events")).toBeInTheDocument();
    expect(screen.getByText(/Annual Science, STEM & Innovation Expo/i)).toBeInTheDocument();
    expect(screen.getByText(/Tarang 2026 — Annual Inter-House Athletic Meet/i)).toBeInTheDocument();
    expect(screen.getByText(/Udaan 2026 — Annual Literary & Performing Arts Fest/i)).toBeInTheDocument();
  });
});

describe("Public Website - Gallery Page", () => {
  it("renders responsive media grid with filter tabs and lightbox trigger cards", () => {
    render(
      <MemoryRouter initialEntries={["/gallery"]}>
        <GalleryPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Sunrise Campus Gallery")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^All Showcases/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Campus & Architecture/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Classrooms & Labs/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Sports & Athletics/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Cultural & Arts/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Events & Festivals/i })).toBeInTheDocument();
  });
});

describe("Public Website - Contact Page", () => {
  it("renders campus address, clickable phone dialer link, office timings, and enquiry form", () => {
    render(
      <MemoryRouter initialEntries={["/contact"]}>
        <ContactPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Contact Sunrise School")).toBeInTheDocument();
    expect(screen.getByText(/Sector 4, Gomti Nagar/i)).toBeInTheDocument();

    const phoneLinks = screen.getAllByRole("link", { name: /\+91 522 299 0000/i });
    expect(phoneLinks[0]).toHaveAttribute("href", "tel:+915222990000");

    expect(screen.getByText(/Monday – Friday: 8:00 AM – 3:30 PM/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Parent \/ Guardian Full Name/i), { target: { value: "Sunil Verma" } });
    fireEvent.change(screen.getByLabelText(/Email Address/i), { target: { value: "sunil.verma@example.com" } });
    fireEvent.change(screen.getByLabelText(/Mobile \/ WhatsApp Number/i), { target: { value: "9876543210" } });
    fireEvent.change(screen.getByLabelText(/Your Message \/ Query/i), { target: { value: "Interested in Class 6 admission." } });

    const submitBtn = screen.getByRole("button", { name: /Submit Enquiry/i });
    fireEvent.click(submitBtn);

    expect(screen.getByText("Enquiry Received Successfully!")).toBeInTheDocument();
    expect(screen.getByText(/Sunil Verma/i)).toBeInTheDocument();
  });
});

describe("Public Website - Public Disclosure Page", () => {
  it("renders 6 mandatory categories, demo information disclaimer, and one-page PDF downloads", () => {
    render(
      <MemoryRouter initialEntries={["/public-disclosure"]}>
        <PublicDisclosurePage />
      </MemoryRouter>
    );

    expect(screen.getByText("Mandatory Public Disclosure")).toBeInTheDocument();
    expect(screen.getByText(/Demonstration Disclosure Notice:/i)).toBeInTheDocument();

    // Tab buttons
    expect(screen.getByRole("button", { name: "A. General Information" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "B. Documents & Information" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "C. Results & Academics" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "D. Staff & Faculty" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "E. Infrastructure" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "F. Student Support & Grievance" })).toBeInTheDocument();

    // Check General tab values
    expect(screen.getByText("Sunrise School (Sunrise Public School)")).toBeInTheDocument();
    expect(screen.getByText(/To be configured \(Demo information\)/i)).toBeInTheDocument();
    expect(screen.getByText("Dr. Ananya Sengupta, M.Sc., M.Ed., Ph.D.")).toBeInTheDocument();

    // Switch to Documents tab
    fireEvent.click(screen.getByRole("button", { name: "B. Documents & Information" }));
    expect(screen.getByText("Mandatory Public Disclosure Summary (Appendix-IX)")).toBeInTheDocument();
    expect(screen.getByText("Approved Annual Fee Structure Schedule 2026–27")).toBeInTheDocument();
    const downloadBtns = screen.getAllByRole("link", { name: /Download PDF \(1 Page\)/i });
    expect(downloadBtns.length).toBeGreaterThanOrEqual(1);
  });
});

describe("Public Website - Resources Page", () => {
  it("renders all 6 approved resources and explicitly excludes parent information PDF", () => {
    render(
      <MemoryRouter initialEntries={["/resources"]}>
        <ResourcesPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Resources & Downloads Hub")).toBeInTheDocument();

    // Approved resources:
    expect(screen.getByText("School Prospectus 2026–27")).toBeInTheDocument();
    expect(screen.getByText("Academic Calendar 2026–27")).toBeInTheDocument();
    expect(screen.getByText("Admission Guidelines & Age Norms")).toBeInTheDocument();
    expect(screen.getByText("Approved Fee Structure 2026–27")).toBeInTheDocument();
    expect(screen.getByText("Curriculum & Syllabus Overview")).toBeInTheDocument();
    expect(screen.getByText("Mandatory Public Disclosure (Appendix-IX)")).toBeInTheDocument();

    // Prohibited resource: Parent Information PDF must NOT exist
    expect(screen.queryByText(/Parent Information PDF/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Parent Information Guide/i)).not.toBeInTheDocument();
  });
});

describe("Public Website - Announcements Page", () => {
  it("renders circulars and announcements search bar and category filters", () => {
    renderWithClient(
      <MemoryRouter initialEntries={["/announcements"]}>
        <AnnouncementsPage />
      </MemoryRouter>
    );

    expect(screen.getByText("News & Official Circulars")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search circulars...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "All" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Admission" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Academic" })).toBeInTheDocument();
  });
});

describe("Public Website - Footer", () => {
  it("renders unified 4-column footer with consolidated explore links and no separate Admissions & ERP column", () => {
    const { container } = render(
      <MemoryRouter initialEntries={["/"]}>
        <PublicLayout>
          <div>Page Content</div>
        </PublicLayout>
      </MemoryRouter>
    );

    const footer = container.querySelector("footer")!;
    expect(footer).toBeInTheDocument();

    // School story & affiliation
    expect(within(footer).getByText(/Gomti Nagar, Lucknow • Estd\. 2011/i)).toBeInTheDocument();
    expect(within(footer).getByText(/School Code: To be configured \(Demo\)/i)).toBeInTheDocument();

    // Verify separate "Admissions & ERP" heading column is removed
    expect(within(footer).queryByRole("heading", { name: "Admissions & ERP" })).not.toBeInTheDocument();

    // Explore section now consolidates school pages and public information
    expect(within(footer).getByRole("link", { name: "School Life & Houses" })).toHaveAttribute("href", "/school-life");
    expect(within(footer).getByRole("link", { name: "Events & Calendar" })).toHaveAttribute("href", "/events");
    expect(within(footer).getByRole("link", { name: "Photo Gallery" })).toHaveAttribute("href", "/gallery");
    expect(within(footer).getByRole("link", { name: "Public Disclosure" })).toHaveAttribute("href", "/public-disclosure");
    expect(within(footer).getByRole("link", { name: "Resources & Downloads" })).toHaveAttribute("href", "/resources");
    expect(within(footer).getByRole("link", { name: "News & Announcements" })).toHaveAttribute("href", "/announcements");
    expect(within(footer).getByRole("link", { name: "Contact Us" })).toHaveAttribute("href", "/contact");

    // No ERP login link in footer
    expect(within(footer).queryByText(/Staff & Student ERP Login/i)).not.toBeInTheDocument();

    // Policy links in footer bottom bar
    expect(within(footer).getByText("Mandatory Public Disclosures")).toBeInTheDocument();
    expect(within(footer).getByText("Downloads & Prospectus")).toBeInTheDocument();
  });
});

describe("Public Website - Route Scroll Restoration", () => {
  it("scrolls to top on route change when no hash anchor is present", () => {
    const scrollToMock = vi.fn();
    window.scrollTo = scrollToMock;

    render(
      <MemoryRouter initialEntries={["/about"]}>
        <PublicLayout>
          <div>About Content</div>
        </PublicLayout>
      </MemoryRouter>
    );

    expect(scrollToMock).toHaveBeenCalledWith({ top: 0, left: 0, behavior: "auto" });
  });

  it("smoothly scrolls to target anchor element when hash is present in route", () => {
    const scrollIntoViewMock = vi.fn();
    const targetElement = document.createElement("div");
    targetElement.id = "process";
    targetElement.scrollIntoView = scrollIntoViewMock;
    document.body.appendChild(targetElement);

    render(
      <MemoryRouter initialEntries={["/admissions#process"]}>
        <PublicLayout>
          <div>Admissions Content</div>
        </PublicLayout>
      </MemoryRouter>
    );

    expect(scrollIntoViewMock).toHaveBeenCalledWith({ behavior: "smooth" });

    document.body.removeChild(targetElement);
  });
});
