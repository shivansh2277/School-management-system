# SESSION-HANDOFF-26.md — Sunrise School: Public Website & ERP UI/UX Upgrade

**Date:** 03 October 2026  
**Status:** Completed Session 25 (Admin Dashboard UI Upgrade & Public Website Upgrades Verified) -> Handoff to Session 26 (Public Website Cleanups & Full ERP UI/UX Upgrade)  
**Branch:** `slice/office-feedback`  
**Reference Design:** Admin Dashboard (`web/src/pages/Dashboard.tsx`) is the primary visual reference for the ERP redesign.

---

## 1. Baseline State Completed in Session 25

1. **Admin Dashboard UI Upgrade Verified** (`web/src/pages/Dashboard.tsx`):
   - Redesigned Attendance Overview, Fees Overview, Grievance inspection with modern cards, clean hierarchy, and accurate real-time data calculations.
   - Defaulters modal and Grievance inspect/reply modals fully operational.
   - Retained live Upcoming Events, Recent Notices, and Top Performers.

2. **Public Website Upgrades Verified**:
   - Replaced early-years ratio with `"Personal Attention at Every Stage"`; all ratio figures removed.
   - 4-photo building carousel implemented with 3s auto-advance and crossfade transitions.
   - Principal identity synchronized everywhere to **Dr. Ananya Sengupta, M.Sc., M.Ed., Ph.D.** (Founder remains **Dr. Anand Mohan Shukla**).
   - Realistic Indian educationist portrait in navy suit added for Founder in About section.
   - Demo School Code updated to `DEMO-SS-2026 (Demo Code)` in Public Disclosure and Footer.
   - Universal scroll-to-top verified across all navigation clicks including already-active tabs.

3. **Clean Test & Compilation Baseline**:
   - **Frontend Vitest (`npm test -- --run` in `web/`):** 25/25 test files passed, 135 passed, 2 skipped (100% green).
   - **Backend Pytest (`pytest -q` in `backend/`):** 800 passed, 1 skipped, 0 failed (100% green).
   - **TypeScript Checks (`npx tsc -b` in `web/`):** 0 errors (clean build).

---

## 2. Session 26 Scope & Requirements

### Section A: Public-Facing Website Cleanups
1. **Homepage Carousel Overlays**:
   - Remove the slide counter badge (`1/4`, `2/4`, etc.) from top-right corner of hero carousel.
   - Remove the image-description caption badge from bottom-left corner.
   - Preserve the 4 Sunrise School building photographs, architectural consistency, and 3-second automatic slide interval.
   - Preserve hero text readability, navigation dots, and smooth crossfade transitions.
2. **Preserve Established Website Design**:
   - Do not redesign unrelated sections, navigation structure, branding, or navy/terracotta identity.

### Section B: ERP Sidebar Improvements
3. **Consistent Icons Across Every Sidebar Option**:
   - Audit `web/src/layout/NavIcons.tsx` and `web/src/screens.ts`.
   - Replace every placeholder circle (`°`), missing icon, or fallback circle dot with a professional, distinct, meaningful SVG icon.
   - Cover all modules: Holidays, Admission Exceptions, Students, Staff, Attendance, Exams, Fees, Transport, Library, Inventory, Certificates, Settings, Rollover, Reception sub-items, etc.
   - Retain golden-amber `#ffa726` accent on dark navy `#042954` sidebar background with consistent 18px size and 2px stroke weight.
4. **Consistent Right-Facing Chevrons**:
   - Add a right-facing chevron (`>`) to every sidebar option in `web/src/layout/Shell.tsx`, aligned neatly at the right edge.
   - Submenu/expandable items: rotate chevron down when open.
   - Leaf items: display right-facing chevron as a consistent navigation indicator without fake expansion.
   - Preserve active (`#ffa726`), hover, and selected states.

### Section C: Complete ERP Visual Redesign
5. **System-Wide Audit & Consistency**:
   - Audit all ERP pages: Admissions, Students, Staff, Attendance, Fees, Exams/Academics, Transport, Library, Inventory, Certificates, Settings, Rollover, Reception, etc.
   - Bring all pages up to the high visual standard established by the upgraded Admin Dashboard (`web/src/pages/Dashboard.tsx`).
6. **Consistent Visual Design System**:
   - **Colors:** Deep navy blue (`#042954`, `text-slate-900`) for headers, blue/teal accents, restrained terracotta/gold highlights.
   - **Surfaces & Backgrounds:** Use subtle tinted backgrounds (`bg-[#f8fafc]` / `bg-canvas`), clean white cards (`bg-white` / `bg-surface`), subtle borders (`border-slate-200/80`), soft shadows (`shadow-xs` / `shadow-card`), rounded corners (`rounded-xl` / `rounded-card`). Eliminate vast plains of stark, unstyled white.
   - **Typography:** Strong hierarchy for titles, subtitles, section headers, table headers, labels, and helper copy.
   - **Status Badges:** Consistent, attractive pill badges for statuses (`Active`, `Pending`, `Approved`, `Rejected`, `Paid`, `Overdue`, `Present`, `Absent`).
   - **Tables:** Styled table headers, subtle row dividers, hover states, clear cell alignment, and contextual action buttons.
   - **Forms:** Group related inputs into organized sections with consistent borders, focus rings, labels, and validation styling.
   - **Buttons:** Standardized primary, secondary, destructive, and icon buttons.
   - **Empty States:** Meaningful empty state cards with helpful guidance rather than blank containers.
7. **Module-Specific Tailored Layouts**:
   - Admissions: Cycle summary cards, status badges, application pipeline/table.
   - Students & Staff: Clean filter toolbars, structured data tables, profile summaries, badge statuses.
   - Attendance: Metric summary cards, attendance distribution visualizers, clear register tables.
   - Fees & Accounts: Financial summary cards, collection progress, organized ledger/roster tables.
   - Exams & Academics: Timetable panels, exam schedules, grading scales, results overview.
   - Transport: Vehicle/route summary cards, structured route stops.
   - Settings & Admin: Well-defined grouped configuration sections.
8. **Restraint & Polish**:
   - Purposeful color, high readability, responsive layouts across desktop (1440px), laptop (1024px), tablet (768px), and mobile.

### Section D: Invariants & Non-Negotiable Rules
- **No Functional Regressions:** Retain all existing routes, navigation, auth, RBAC, tenant isolation, APIs, queries, form submissions, and modals.
- **Real Data Only:** No hardcoded numbers or fake statistics.
- **Workflow Rule:** In the next session, the assistant must FIRST produce a comprehensive, detailed implementation plan and obtain user approval before modifying code.

---

## 3. Key Codebase Anchors

- `web/src/pages/public/website/HomePage.tsx`: Hero carousel slide counter & caption badge removal.
- `web/src/layout/Shell.tsx`: Sidebar navigation rendering and chevron alignment.
- `web/src/layout/NavIcons.tsx`: Icon definitions and default icon replacement.
- `web/src/screens.ts`: Route list and navigation definitions.
- `web/src/pages/Dashboard.tsx`: Primary design reference for ERP cards, typography, tables, and metric pills.
- `web/src/pages/`: All ERP screen modules (`Admissions`, `Students`, `Staff`, `Attendance`, `Fees`, `Exams`, `Transport`, `Library`, `Inventory`, `Certificates`, `Settings`, `HolidayManagement`, etc.).
