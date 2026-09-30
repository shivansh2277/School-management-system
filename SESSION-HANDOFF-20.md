# SESSION-HANDOFF-20: Sunrise School ERP Status & Next Directives

> **Target Session:** Session 20  
> **Status:** COMPLETED & VERIFIED — READY FOR NEXT DIRECTIVES  
> **Canonical Branch:** `slice/office-feedback` (synced with `origin/main`)  
> **Current Verified Baseline:**  
> - Backend Tests: **769 passed, 2 skipped, 0 failed** (`../.venv/Scripts/python.exe -m pytest -q`) — 100% green  
> - Backend Alerts Tests: **10 passed, 0 failed** (`tests/test_alerts.py`) — 100% green  
> - Web Tests: **109 passed, 2 skipped** across 20 files (`npm test` in `web/`) — 100% green  
> - Web Typecheck: **0 errors** (`npx tsc --noEmit` in `web/`)  
> - Mobile Typecheck: **0 errors** (`npm run typecheck` in `mobile/`)  
> - Visual Verification Suite: **13 screenshots captured & verified** (7 from Session 19 in `docs/screenshots/session19/` and 6 from Session 20 in `docs/screenshots/session20/` and persistent artifact directory)  

---

## 1. Session 19 Deliverables Summary

All requirements specified for Session 19 (including the extended Persistent Alert Lifecycle) were successfully engineered, tested, and visually confirmed:

### Domain 1: Website — Redesigned Sidebar Section Headings (`web/src/layout/Shell.tsx`)
- Replaced faint, low-contrast grey text (`text-white/50`) with high-contrast, polished typography (`text-[11px] font-bold text-white/90 uppercase tracking-wider`).
- Added vertical school branding pill accent (`w-1 h-3 rounded-full bg-blue-300/80 mr-2 shrink-0`).
- Added hairline divider rule (`flex-1 h-px bg-white/10 ml-2`) for subtle horizontal division between logical ERP sections.
- Maintained strict structural role (`role="presentation"`) with zero modifications to routing, permissions, or screen definitions in `web/src/screens.ts`.
- Visually verified across Admin (`session19_web_admin_sidebar.png`) and Receptionist (`session19_web_receptionist_sidebar.png`) roles.

### Domain 2: Mobile App — Roadmap Future Feature Placeholders (`mobile/src/components/NavDrawer.tsx`)
- Added disabled, non-interactive placeholder items with a rounded "Coming Soon" pill (`bg-indigo-50`, `border-indigo-100`, text `indigo-600`):
  - **Parent Role** (under `COMMUNICATION`):
    - `Call Class Teacher` (Future roadmap: native phone dialer `tel:`)
    - `Message Class Teacher` (Future roadmap: 2-way chat with class teacher)
  - **Teacher Role**:
    - Under `ACADEMICS`: `Today's Class` (Future roadmap: daily class log)
    - Under `COMMUNICATION`: `Parent Messages` (Future roadmap: 2-way teacher-parent messaging)
  - **Student Role** (under `ACADEMICS`):
    - `Today's Class` (Future roadmap: read-only daily class notes)
    - **Child Safety Compliance**: Students are strictly prevented from direct teacher messaging.
- Bilingual localization: Full English and Hindi support in `mobile/src/i18n/translations.ts` (`en: "Coming Soon"`, `hi: "जल्द आ रहा है"`).

### Domain 3: Student & Parent Home — Important Alerts System & Persistent Lifecycle
- **Alert Engine (`backend/app/services/alerts.py`)**:
  - Pure calculation service evaluating student alerts:
    1. **Attendance Shortage Alert**: Triggered strictly when `attendance_pct < 75.0` (`danger` / `#dc2626` / `⚠️`). Clears when viewed. Stored with event key `att-{absent_count}-{latest_date}`: if a new absence occurs or absence count increments, the key advances and a new alert reappears.
    2. **Fee Due Alert (STRICT EXCEPTION)**: Triggered when `fee_due > 0.0` (`warning` / `#d97706` / `💰`). Formats outstanding amount in INR. **CANNOT be dismissed by viewing or tapping**. Persists until balance reaches zero.
    3. **Report Card Available Alert**: Triggered when a published terminal exam report card exists (`info` / `#4f46e5` / `📄`). Clears permanently once viewed.
    4. **Periodic Test Result Available Alert**: Triggered when a published periodic test (PT) exam result exists (`info` / `#0284c7` / `📊`). Clears permanently once viewed.
- **Database Model & Migration (`alert_views` table)**:
  - Model: `AlertView(TenantBase)` in `backend/app/models/notification.py` storing `(school_id, user_id, student_id, alert_type, event_key, viewed_at)` with unique constraint.
  - Migration Head: `c4d5e6f7a8b9`.
- **Backend API Endpoints**:
  - `GET /student/dashboard`: Returns unviewed alerts array, fee due amount, and latest exam flags.
  - `GET /parent/children/{id}/summary`: Enriched with alert contract fields filtered by viewed state.
  - `GET /parent/alerts`: Evaluates unviewed alerts across all children in `me.children` for multi-child parents, with child attribution (`child_id`, `child_name`).
  - `POST /student/alerts/view`: Records viewed state for student (refuses fee alerts).
  - `POST /parent/alerts/view`: Records viewed state for parent per child (refuses fee alerts).
- **Mobile Component (`mobile/src/components/ImportantAlerts.tsx`)**:
  - Color-coded card layout with left accent border (`borderLeftWidth: 4`), emoji icons, chevron indicator, and red accent header badge.
  - **Zero Empty Container Invariant**: Fully collapses (`null`) when no alerts apply.
- **Parent Multi-Child Integration & Navigation**:
  - Displays child attribution directly in alert card headers (e.g. `Fee Due — Aarav Sharma`, `Report Card Available — Ishita Sharma`).
  - **Synchronous Context Switch Invariant**: Tapping an alert triggers `selectChild(alert.child_id)` before calling `router.push(alert.route)` so destination screens load the correct child's context.
### Domain 4: Website — Redesigned Solid Dark-Blue Navigation Sidebar (Akkhor Theme Pattern)
- **Sidebar Background**: Changed from purple `bg-primary` to solid dark-blue (`#042954`).
- **Brand Header Bar**: Vibrant amber/orange banner (`bg-gradient-to-r from-[#ffa726] to-[#fb8c00]`, `h-14`) with a circular white crest badge (`w-8 h-8 rounded-full bg-white flex items-center justify-center`), bold white uppercase "SUNRISE" header, and "PUBLIC SCHOOL" subtitle. Cleanly displays only school branding with no hamburger button inside the sidepanel across all screens (mobile, tablet, laptop) and roles. Toggle button remains in the main top header bar.
- **Navigation Items (`web/src/layout/NavIcons.tsx`, `web/src/layout/Shell.tsx`)**:
  - **Icons**: Custom golden-amber SVG icons (`text-[#ffa726]`, `18x18px`) for every screen route.
  - **Labels**: Clean typography (`text-[#c2d0e2]`, hovering to `text-white`).
  - **Right-Facing Chevrons `>`**: Displayed on items with expandable/sub-navigation or multi-view hubs (`screenHasChevron(path)`), matching the Akkhor template reference pattern.
  - **Item Separators**: Hairline horizontal dividers (`border-b border-white/[0.03]`) and section boundaries for a structured, professional vertical rhythm.
  - **Active / Highlighted State**: Active route highlighted with deep navy background (`bg-[#021b38]`), vibrant amber text (`text-[#ffa726] font-semibold`), amber chevron, and a solid left accent border (`border-l-4 border-l-[#ffa726] pl-[10px]`).
- **Section Headings**: Visually distinct, non-clickable structural headers (`text-[10px] font-bold text-blue-200/50 uppercase tracking-widest`) with amber vertical pill accent (`w-1 h-2.5 rounded-full bg-[#ffa726]/80`) and hairline horizontal rule.
- **Responsive Behavior**: Desktop collapsible rail/drawer (`w-60` vs `w-0 invisible`), mobile off-canvas drawer with dark backdrop overlay (`bg-black/60`), and synchronized toggles.
- **Role & Route Integrity**: Zero changes to permissions, screens registry, or RBAC routing.

---

## 2. Test Verification Matrix

| Test Suite | Commands | Result |
|---|---|:---:|
| **Full Backend Pytest** | `..\.venv\Scripts\python.exe -m pytest -q` | **769 passed, 2 skipped** (100% green) |
| **Backend Alerts Suite** | `..\.venv\Scripts\python.exe -m pytest tests/test_alerts.py -v` | **10 passed in 21s** (100% green) |
| **Web Vitest Suite** | `npm test` in `web/` | **109 passed, 2 skipped** (100% green) |
| **Web Typecheck** | `npx tsc --noEmit` in `web/` | **0 errors** |
| **Mobile Typecheck** | `npm run typecheck` in `mobile/` | **0 errors** |
| **Sidebar Visual Verification** | `node verify_redesigned_sidebar.mjs` in `web/` | **6/6 captured & verified** |

---

## 3. Visual Verification Artifacts

### Session 20: Redesigned Dark-Blue Sidebar Suite (`docs/screenshots/session20/`)
1. `session20_sidebar_admin_expanded.png`: Desktop Admin view showing solid dark-blue `#042954` sidebar, amber brand bar, white circular emblem, hamburger toggle, golden icons, chevrons, and active Dashboard state.
2. `session20_sidebar_active_page.png`: Active page state on `/students` with amber text, active bed, and left border accent.
3. `session20_sidebar_admin_collapsed.png`: Desktop collapsed state after clicking hamburger toggle.
4. `session20_sidebar_admin_reopened.png`: Desktop reopened state after toggling again.
5. `session20_sidebar_receptionist.png`: Role-specific Front Desk & Receptionist sidebar view.
6. `session20_sidebar_mobile_drawer.png`: Mobile view showing responsive drawer with backdrop overlay.

### Session 19: Alerts, Badges & Sidebar Suite (`docs/screenshots/session19/`)
1. `session19_web_admin_sidebar.png`: Admin section headings with navy pill accents and hairline dividers.
2. `session19_web_receptionist_sidebar.png`: Receptionist section headings.
3. `session19_mobile_student_dashboard.png`: Student Home Important Alerts (Fee Due, Report Card, Periodic Test).
4. `session19_mobile_student_drawer.png`: Student NavDrawer showing "Today's Class" Coming Soon pill (no teacher messaging).
5. `session19_mobile_parent_dashboard.png`: Parent Home multi-child Important Alerts with child attribution pills.
6. `session19_mobile_parent_drawer.png`: Parent NavDrawer showing "Call Class Teacher" and "Message Class Teacher" Coming Soon pills.
7. `session19_mobile_teacher_drawer.png`: Teacher NavDrawer showing "Today's Class" and "Parent Messages" Coming Soon pills.

---

## 4. Key Architectural Patterns & Invariants to Preserve

1. **Attendance Shortage Threshold Testing**:
   - Never insert raw `Attendance` rows in tests for existing dates; mutate existing attendance status (`absent` / `present`) to avoid `uq_attendance_enrolment_date` violations.
2. **Synchronous Context Switching on Parent Mobile**:
   - Alerts spanning multiple children must call `selectChild(alert.child_id)` synchronously before pushing the navigation route.
3. **Child Safety Messaging Boundary**:
   - Students must **never** be given direct messaging capabilities with teachers. Student interaction with teacher class logs is strictly read-only.
4. **Zero Empty Container Invariant**:
   - The alert container must return `null` when alert count is 0 to avoid empty boxes or blank borders in mobile dashboards.
