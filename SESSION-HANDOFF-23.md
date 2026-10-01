# SESSION-HANDOFF-23: Sunrise School Institutional Public Website & ERP Admission Integration

> **Target Session:** Session 23  
> **Status:** COMPLETED & FULLY VERIFIED (BACKEND TESTS 778/778, WEB TESTS 125/125, ZERO TS ERRORS, PRODUCTION BUILD CLEAN, 15 DESKTOP/TABLET/MOBILE SCREENSHOTS CAPTURED)  
> **Canonical Path:** `school-management-system/`  
> **Current Verified Baseline:**  
> - Backend Tests: **778 passed, 1 skipped, 0 failed** (`.venv\Scripts\pytest.exe -q`) — 100% green  
> - Web Tests: **125 passed, 2 skipped** across 21 test files (`npm test -- --run` in `web/`) — 100% green  
> - Web Typecheck: **0 errors** (`npx tsc --noEmit` in `web/`)  
> - Production Bundle: **Clean Vite build** (`npm run build` in `web/`) in 10.21s  
> - Visual Verification Suite: **15 visual screenshots captured** across Desktop (1440x900), Tablet (768x1024), and Mobile (390x844) stored in `docs/screenshots/session23/` and conversation artifacts.  

---

## 1. Executive Summary of Session 23

Session 23 executed an institutional refinement pass on the public-facing Sunrise School website based on Central Academy reference research, user requirements, and screenshot references (`media_1790748713854.jpg`):

1. **Classy Institutional Primary Navigation & ERP Login CTA**:
   - Refined to 9 canonical links: `Home`, `About`, `Academics`, `Admissions`, `Campus & Facilities`, `School Life`, `Events`, `Public Disclosure`, `Resources`.
   - Header right action is **`ERP Login →`** routing to `/login` using the existing Sunrise ERP login route (clean primary button on desktop and compact header/drawer button on mobile).
   - Purged `Contact` (contact details permanently anchored in the 4-column footer).
   - Purged `Gallery` from navbar (photographic gallery merged directly into School Life at `/school-life#gallery`).
   - Mobile navigation drawer includes one-tap `tel:+915222990000` phone dialer, `ERP Login →`, and `Apply Online Portal`.

2. **Persistent Admission Enquiry Side CTA (`AdmissionSideCTA.tsx`)**:
   - Subtle, premium, clearly visible side block across public informational pages (`AdmissionSideCTA.tsx`).
   - Desktop/tablet: Vertical tab docked on right edge with gold border, pencil icon, vertical tracking, and `26–27` badge.
   - Mobile: Compact, non-intrusive floating pill docked at `bottom-5 right-4` with amber gold gradient, icon, and pulsing badge.
   - Isolated from `/apply` and `/login` workflows.
   - Submits directly to the ERP enquiry backend workflow (`POST /public/{school_code}/admission/enquiry`).

3. **School Life & Photo Gallery Merged (`/school-life`)**:
   - Merged editorial photo gallery into the bottom of School Life (`#gallery`).
   - 5 Category filter tabs: `All`, `Campus`, `Classrooms & Labs`, `Sports & Athletics`, `Arts & Culture`.
   - Lightbox modal with next/prev navigation, category tags, and photo captions.

4. **Public Admission Enquiry Integrated Directly with ERP Backend**:
   - Single source of truth: Writes directly to the ERP `enquiries` table (`backend/app/models/reception.py`) without duplicate models or workflows.
   - Endpoint: `POST /public/{school_code}/admission/enquiry` in `backend/app/api/public/admission.py`.
   - Model invariants: `source = EnquirySource.website`, `status = EnquiryStatus.new`.
   - Duplicate resolution: If an enquiry with the same mobile exists within the active cycle, appends notes as a new `EnquiryInteraction` (`occurred_at=datetime.now(UTC)`) without creating duplicate student records.
   - Returns unique reference: `ENQ-{enquiry.id:04d}`.
   - Frontend modal (`AdmissionEnquiryModal.tsx`) with form validation and success confirmation.

5. **Global Dark-Blue Announcement Strip**:
   - Placed globally in `PublicLayout.tsx` beneath `PublicNavbar` across all public pages.
   - Strictly excluded from `/apply` (`PublicApplyPage.tsx`) to maintain an undistracted admission application experience.
   - Live ticker with gold `ANNOUNCEMENT` badge and link to `/announcements`.

6. **News & Announcements Fallback & Seeding**:
   - Seeded with realistic circulars across 7 categories: `Admission`, `Academic`, `Achievement`, `Event`, `Holiday`, `Notice`, `General`.
   - Client-side resilient fallback (`DEFAULT_ANNOUNCEMENTS`) in `AnnouncementsPage.tsx` and `AnnouncementDetailPage.tsx` ensuring catalog and circular views are never blank.

7. **Expanded About Page Institutional Narrative**:
   - Detailed institutional history (2011–2026).
   - Founder Profile: Dr. Anand Mohan Shukla (Founding Trustee) with portrait (`/images/school/founder_portrait.jpg`), biography, and founding philosophy.
   - Founder's Quote Card & 6-step institutional milestones timeline.
   - 7-C Educational Philosophy: Curiosity, Critical Thinking, Character, Creativity, Collaboration, Communication, Confidence.

8. **Hero Photography & Principal Welcome Matching Reference**:
   - 4 authentic Sunrise School photographs matching `media_1790748713854.jpg`: Modern Classroom, Composite Science Lab, Teacher Mentorship, Athletics/Sports Field.
   - Principal Dr. Meera Sharma welcome message and quote card.

---

## 2. Screenshot Manifest

All 15 visual screenshots have been saved to `docs/screenshots/session23/` and copied to the conversation artifact directory:

| Filename | Description | Resolution |
| :--- | :--- | :--- |
| `01_desktop_home_hero.png` | Desktop Home Hero with 9-link navbar, ERP Login button, announcement strip, and persistent right-edge Side CTA | 1440 × 900 |
| `02_desktop_home_features_principal.png` | Desktop 4-Photo Feature Grid matching reference & Principal Dr. Meera Sharma | 1440 × 900 |
| `03_desktop_admission_enquiry_modal.png` | Desktop Admission Enquiry Modal opened via persistent Side CTA | 1440 × 900 |
| `04_desktop_about_overview.png` | Desktop Expanded About Page Hero & persistent Side CTA on informational pages | 1440 × 900 |
| `05_desktop_about_founder_section.png` | Desktop Founder Dr. Anand Mohan Shukla portrait, quote card & milestones | 1440 × 900 |
| `06_desktop_school_life_houses.png` | Desktop School Life House System & Co-curricular overview | 1440 × 900 |
| `07_desktop_school_life_merged_gallery.png` | Desktop Merged Editorial Photo Gallery with category tabs & Lightbox | 1440 × 900 |
| `08_desktop_announcements_catalog.png` | Desktop News & Announcements catalog with category filters | 1440 × 900 |
| `09_tablet_home.png` | Tablet Home Hero with ERP Login in header & persistent Side CTA | 768 × 1024 |
| `10_tablet_about_founder.png` | Tablet About Page Founder section & institutional milestones | 768 × 1024 |
| `11_mobile_home.png` | Mobile Home with ERP Login header button & compact floating Admission Enquiry CTA | 390 × 844 |
| `12_mobile_navbar_drawer_open.png` | Mobile 9-Link Navigation Drawer with ERP Login & Apply Online Portal | 390 × 844 |
| `13_mobile_admission_enquiry_modal.png` | Mobile Admission Enquiry Modal dialog opened via floating CTA | 390 × 844 |
| `14_mobile_school_life_gallery.png` | Mobile School Life Merged Gallery | 390 × 844 |
| `15_desktop_apply_workflow_no_cta.png` | Desktop `/apply` Admission Workflow strictly isolating without Side CTA or announcement strip | 1440 × 900 |

---

## 3. Mandatory Workflow Constraint for Session 24

> [!IMPORTANT]
> **CRITICAL INSTRUCTION FOR NEXT AGENT SESSION:**
> **FIRST generate a detailed, comprehensive implementation plan and present it to the user. Do NOT write code, create database migrations, or make any changes until the user explicitly reviews and approves the implementation plan.**

---

## 4. Scope for Next Session (Session 24)

### Topic: Admission Documents, APAAR ID, Student ID Cards, Certificates & Holiday Management

1. **Admission Form — Conditional Birth Certificate Requirement**:
   - **Business Rule**: Birth certificate mandatory IF applying for junior section through UKG inclusive, OR age < 5 on session admission date. Optional otherwise.
   - Dynamic calculation based on selected class and DOB using existing session age rules (no hardcoded calculation).
   - Validated on both frontend and backend.
   - **Admin Override Mechanism**: Authorized Admin override for missing mandatory documents with required reason recorded in audit log (`document_type`, `application_id`, `user_id`, `timestamp`, `reason`).
   - **RBAC Preservation**: Keep normal application processing with Admission Cell; Admin override is a narrowly scoped exception permission, NOT general application processing access.
   - Works on both public admission website (`/apply`) and internal ERP application workflows.

2. **APAAR ID and Parental Consent**:
   - Required section in admission workflow.
   - Distinct states: (1) Existing APAAR ID provided, (2) Parental consent to facilitate APAAR creation on student's behalf, (3) Authorized document override.
   - Clear distinction: Consent != existing APAAR ID.
   - Validated frontend + backend; metadata captures consenting guardian and timestamp for audit.
   - APAAR ID can be updated later without creating duplicate student records. Never invent or auto-generate local fake IDs.
   - Managed by Admission Cell; Admin override applies for exceptions.

3. **Student ID Card Generation**:
   - Canonical Identifier: Use **Enrollment ID** printed on the card (no second ID or library card number).
   - Card content: School logo and name, student photo, student name, Enrollment ID, class & section, academic session, QR code/barcode encoding Enrollment ID.
   - Graceful handling of missing photos.
   - Workflows: Individual generation from student profile + Bulk generation by class/section/session.
   - Print-ready layout / PDF generation using existing ReportLab / PDF stack.

4. **Library Module — Use Enrollment ID Instead of Separate Library Card**:
   - Primary physical card is the Student ID card.
   - Lookup student by Enrollment ID or scan QR code/barcode.
   - Retire separate library-card generation/number system while safely mapping existing loans and preserving historical borrowing records.
   - Physical card not required to be printed for a student to be eligible to borrow.

5. **Admin-Managed Student Certificates**:
   - Types: (1) Transfer Certificate (TC), (2) Character Certificate, (3) Bonafide Certificate.
   - RBAC: Admin and authorized staff (Principal where permitted); not open to all staff.
   - Workflows: Direct issuance by authorized users + Request-and-approval workflow.
   - Configurable certificate templates with institutional branding, certificate number, issue date, student details, and signatory.
   - Audit trail and immutable issuance history (corrections/reissues must be audited).
   - **TC Invariants**: Clear confirmation explaining exit consequences; updates student exit date and lifecycle status atomically; preserves academic, fee ledger, payment, and library records (never delete student). Character/Bonafide certificates do not modify student status.

6. **Holiday Management Integrated With Attendance**:
   - Admin section to declare, edit, and cancel holidays (school-wide or class/section-scoped) for an academic session.
   - Before attendance marking, check holiday applicability; block attendance marking and display holiday name across Web ERP, Mobile App, and Backend APIs.
   - Narrowly scoped Admin override for special classes held on holidays (reason + audit trail).
   - Attendance reports/summaries must not treat holidays as student absence.
   - Preserves existing attendance records if a holiday is declared retroactively.
   - Mobile app integration for teachers with offline queue validation.

---

## 5. Verification Commands for Session 24

```powershell
# 1. Backend Pytest
cd school-management-system
..\.venv\Scripts\pytest.exe -q

# 2. Frontend Unit Tests & Typecheck
cd web
npm test -- --run
npx tsc --noEmit
npm run build

# 3. Mobile Typecheck
cd ../mobile
npm run typecheck
```
