# SESSION-HANDOFF-9: Mobile Navigation Redesign, Admin Fee Chart Removal, Teacher Recruitment Deletion, and Global Red-X Close Controls

> **Target Implementation Session:** Session 9  
> **Status:** READY FOR EXECUTION  
> **Branch:** `slice/office-feedback` (strictly local development; NEVER push to remote)  
> **Backend Test Baseline:** 731 passed, 1 skipped, 0 failed (100% green with `school-management-system/.venv/Scripts/python.exe -m pytest -q`)  
> **Web Test Baseline:** 85 passed across 19 test files (100% green with `npm test` in `web/`)  
> **Mobile Typecheck Baseline:** Clean (`npm run typecheck` in `mobile/`)  
> **Web Typecheck Baseline:** Clean (`npx tsc --noEmit` in `web/`)  
> **Corpus / Repository Root:** `c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`  

---

## 0. AUTHORITATIVE PRODUCT OVERRIDES & LOCKED INVARIANTS

The following 5 requirements define the scope of Session 9. Implementations must follow the established Sunrise ERP architecture, tenant isolation, role-based access control, database relationships, and UI design tokens. Superficial UI-only fixes, duplicate models, or broken routes are strictly prohibited.

1. **Mobile Navigation Redesign (Strict 4 Bottom Tabs + Top-Left Hamburger Drawer):**
   - The current mobile app has too many features crowded into the bottom navigation bar (9 tabs on Parent, 11 tabs on Teacher, 7 tabs on Student).
   - Redesign navigation across all three roles using a unified architectural pattern:
     - A **hamburger icon at the top-left** of the header that slides open a full, categorized drawer menu.
     - An uncluttered **4-item bottom navigation bar** tailored specifically to each role:
       - **Parent:** `Home`, `Child`, `Fees`, `Profile`
       - **Teacher:** `Home`, `Classes`, `Attendance`, `Profile`
       - **Student:** `Home`, `Timetable`, `Homework`, `Profile`
   - **Zero Feature Loss Invariant:** Every existing feature remains 100% functional and accessible via the hamburger drawer menu according to existing permissions.
   - **Strict Role Isolation Invariant:** Never leak Parent-only, Teacher-only, or Student-only features to another role.
   - Routes moved out of the bottom bar are configured with `href: null` in Expo Router's `<Tabs.Screen>` so they remain registered, deep-linkable, and stack-routable via `router.push()`.
   - Follow the visual/interaction pattern of the Acharya Prashant reference: top-left hamburger icon → slide-over drawer → user profile header (name, role badge, initials avatar) → categorized menu sections → smooth close on item selection or backdrop press. Maintain Sunrise ERP design tokens (`theme.primary`, `theme.surface`, `theme.ink`, `theme.rule`).

2. **Website — Remove Fee Collection Graph from Admin Dashboard:**
   - In the Office Administrator / Admin dashboard (`web/src/pages/Dashboard.tsx`), completely remove the "Fee Collection" bar chart/graph (`<Card title="Fee Collection">` containing `ResponsiveContainer` and `BarChart`).
   - Remove the entire component and its card placement.
   - Do **NOT** replace it with another graph or leave an empty whitespace container.
   - Safely clean up any dashboard-specific unused chart imports from `recharts` in `Dashboard.tsx`.
   - Preserve all other dashboard functionality (Attendance Overview, KPI stats, Defaulters modal, Grievance feed, etc.).
   - Do **NOT** modify or delete underlying fee services, ledger tables, or counter fee data.

3. **Complete Purge of Teacher Recruitment:**
   - Teacher Recruitment is **permanently decommissioned** from the product.
   - **Frontend:** Remove `/recruitment` route from `web/src/screens.ts`, delete `web/src/pages/RecruitmentPage.tsx`, delete `web/src/pages/RecruitmentPage.test.tsx`, and delete `web/src/components/recruitment/`. Remove candidate intake actions from receptionist scripts and UI.
   - **Backend:** Remove `backend/app/api/admin/recruitment.py`, `backend/app/services/recruitment.py`, `backend/app/models/recruitment.py`, router registration in `backend/app/main.py`, and model exports in `backend/app/models/__init__.py`.
   - **Core Configuration:** Remove `recruitment.candidate.*` permissions from `backend/app/core/permissions.py` (and role assignments for admin, principal, receptionist). Remove `"recruitment"` module from `backend/app/core/modules.py`.
   - **Database & Migrations:** Remove recruitment tables (`candidates`, `candidate_offers`) via a clean Alembic migration or schema cleanup without damaging shared tables (`employees`, `users`, `departments`).
   - **Tests:** Purge recruitment-specific tests from `backend/tests/test_teacher_leave_and_recruitment.py` while preserving 100% of the teacher leave and substitution coverage tests.

4. **Global Replacement of Textual "Close" with Red X:**
   - Throughout the ERP mobile app and web application:
   - Wherever a modal, drawer, dialog, popup, sheet, or overlay currently uses a textual "Close" control:
     - Replace the visible "Close" text with an X / ✕ close icon.
     - Style with an authoritative red tone (`text-red-500` / `#ef4444` / `theme.danger`).
     - Position consistently in the top-right corner of the container.
     - Ensure minimum 44×44px touch ergonomics on mobile (`hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}`).
     - Maintain strict accessibility with `aria-label="Close"` / `accessibilityLabel="Close"`.
     - Invariant: Do **NOT** replace functional action text that merely contains "close" (such as "Period Close" or "Close Account").

5. **Do Not Break Existing ERP:**
   - Inspect all dependencies before deleting or refactoring.
   - Re-verify full test suites (backend pytest, web vitest, mobile & web typecheck) and ensure zero regressions.

---

## 1. DETAILED ENGINEERING SPECIFICATIONS BY TASK

---

### TASK 1 — Mobile App: Redesign Navigation (4 Bottom Tabs + Hamburger Drawer)

#### 1.1 Architectural Pattern
Currently, mobile screens define all features as visible tabs in `Tabs.Screen` inside:
- `mobile/app/(parent)/_layout.tsx` (9 tabs)
- `mobile/app/(teacher)/_layout.tsx` (11 tabs)
- `mobile/app/(student)/_layout.tsx` (7 tabs)

In Expo Router, setting `options={{ href: null }}` on a `<Tabs.Screen>` keeps the route registered and accessible via `router.push('/(role)/screen-name')`, while completely hiding it from the bottom tab bar.

#### 1.2 Shared Navigation Drawer Component
Create a reusable, lightweight drawer component:
- **File:** `mobile/src/components/NavDrawer.tsx`
- **Design & Layout:**
  - Standard React Native `Modal` with `animationType="fade"` or slide-in container covering 80% screen width from the left, with dark semi-transparent backdrop (`rgba(0,0,0,0.5)`).
  - Tapping the backdrop or pressing the top-right **Red X** closes the drawer.
  - **Header / Profile Section:**
    - User avatar / initials circle in `theme.primary`.
    - User full name and role badge (`Parent`, `Teacher`, or `Student`).
    - Active school name / branding subtitle ("Sunrise Public School").
  - **Scrollable Grouped Menu List:**
    - Clean section titles (uppercase, letter-spaced, e.g., `ACADEMICS`, `OPERATIONS`, `COMMUNICATION`, `ACCOUNT`).
    - Interactive rows with `Ionicons`, title, and subtle chevron or active indicator.
    - Tapping an item closes the drawer and calls `router.push(targetPath)`.
  - **Footer:**
    - App version info.
    - Prominent "Logout" button with confirmation alert calling `useAuth().logout()`.

#### 1.3 Role-Specific Configurations

##### A. Parent Navigation
- **Bottom Navigation (Strict 4 Items):**
  1. `dashboard` — **Home** (`home-outline`)
  2. `child` — **Child** (`person-circle-outline`)
  3. `fees` — **Fees** (`card-outline`)
  4. `profile` — **Profile** (`person-outline`)
- **Hidden Tab Routes (`href: null`):**
  - `attendance`, `homework`, `results`, `grievances`, `notices`
- **Hamburger Drawer Menu Structure (Parent):**
  ```text
  ACADEMICS
  - Timetable (calendar-outline) -> /(parent)/child or dedicated timetable
  - Homework (book-outline) -> /(parent)/homework
  - Attendance (checkbox-outline) -> /(parent)/attendance
  - Results / Report Cards (school-outline) -> /(parent)/results

  COMMUNICATION
  - Notices (notifications-outline) -> /(parent)/notices
  - Grievances / Helpdesk (chatbubbles-outline) -> /(parent)/grievances

  OTHER
  - Switch Student (if multiple children)
  - Settings (settings-outline)
  - Support & Help (help-circle-outline)
  - Logout (log-out-outline)
  ```

##### B. Teacher Navigation
- **Bottom Navigation (Strict 4 Items):**
  1. `dashboard` — **Home** (`home-outline`)
  2. `classes` — **Classes** (`people-outline`)
  3. `attendance` — **Attendance** (`checkbox-outline`)
  4. `profile` — **Profile** (`person-outline`)
- **Hidden Tab Routes (`href: null`):**
  - `homework`, `stock`, `grievances`, `results`, `announcements`, `timetable`, `leave`
- **Hamburger Drawer Menu Structure (Teacher):**
  ```text
  ACADEMICS
  - Timetable (calendar-outline) -> /(teacher)/timetable
  - Homework Manager (book-outline) -> /(teacher)/homework
  - Marks Entry / Results (school-outline) -> /(teacher)/results

  OPERATIONS
  - Classroom Supplies / Stock (cube-outline) -> /(teacher)/stock
  - Leave Application & Duties (calendar-clear-outline) -> /(teacher)/leave

  COMMUNICATION
  - School Notices (megaphone-outline) -> /(teacher)/announcements
  - Grievance Desk (chatbubbles-outline) -> /(teacher)/grievances

  OTHER
  - Settings (settings-outline)
  - Support (help-circle-outline)
  - Logout (log-out-outline)
  ```

##### C. Student Navigation
- **Bottom Navigation (Strict 4 Items):**
  1. `dashboard` — **Home** (`home-outline`)
  2. `timetable` — **Timetable** (`calendar-outline`)
  3. `homework` — **Homework** (`book-outline`)
  4. `profile` — **Profile** (`person-outline`)
- **Hidden Tab Routes (`href: null`):**
  - `attendance`, `results`, `notices`
- **Hamburger Drawer Menu Structure (Student):**
  ```text
  ACADEMICS
  - Attendance History (checkbox-outline) -> /(student)/attendance
  - Exam Results & Scorecard (school-outline) -> /(student)/results

  COMMUNICATION
  - School Notices (notifications-outline) -> /(student)/notices

  OTHER
  - Settings (settings-outline)
  - Support (help-circle-outline)
  - Logout (log-out-outline)
  ```

#### 1.4 Hamburger Icon in Headers
- In `_layout.tsx` for each role, configure `headerLeft`:
  ```tsx
  headerLeft: () => (
    <Pressable
      onPress={() => setDrawerOpen(true)}
      style={{ marginLeft: 16, padding: 6 }}
      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      accessibilityRole="button"
      accessibilityLabel="Open Menu"
    >
      <Ionicons name="menu-outline" size={26} color={theme.ink} />
    </Pressable>
  )
  ```
- For Parent layout, preserve `ChildSwitcher` as a secondary banner or integrate cleanly into the header without colliding with the hamburger button.

---

### TASK 2 — Website: Remove Fee Collection Graph from Admin Dashboard

#### 2.1 File & Lines to Modify
- **File:** [`web/src/pages/Dashboard.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/web/src/pages/Dashboard.tsx)
- **Target Section (Lines 465–479):**
  ```tsx
  <Card title="Fee Collection">
    {data.fee_trend.length === 0 ? (
      <Empty>No payments recorded yet.</Empty>
    ) : (
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data.fee_trend.map((p) => ({ ...p, collected: Number(p.collected) }))}>
          <CartesianGrid stroke={theme.rule} vertical={false} />
          <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={12} />
          <YAxis tickLine={false} axisLine={false} fontSize={12} width={70} />
          <Tooltip formatter={(v: number) => money(v)} />
          <Bar dataKey="collected" fill={theme.primary} radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    )}
  </Card>
  ```

#### 2.2 Execution Steps
1. Delete the entire `<Card title="Fee Collection">...</Card>` block.
2. Clean up unused `recharts` imports in `web/src/pages/Dashboard.tsx` (remove `Bar`, `BarChart`, `CartesianGrid`, `ResponsiveContainer`, `Tooltip`, `XAxis`, `YAxis` if no other chart in `Dashboard.tsx` uses them).
3. Ensure no empty grid cell or broken layout is left in `Dashboard.tsx`.
4. Leave backend API `stats.py` (`fee_trend`) intact if other reports or consumers use it, but ensure frontend doesn't trigger visual rendering.
5. In `web/src/pages/Dashboard.test.tsx`, update any test assertions expecting the text `"Fee Collection"`.

---

### TASK 3 — Decommission & Delete Teacher Recruitment

#### 3.1 Complete Dependency Map of Recruitment
Before deleting anything, observe every file touching recruitment:
1. `web/src/screens.ts` (route `/recruitment`, permission `recruitment.candidate.read`, module `recruitment`)
2. `web/src/pages/RecruitmentPage.tsx`
3. `web/src/pages/RecruitmentPage.test.tsx`
4. `web/src/components/recruitment/PrintableApplicationForm.tsx`
5. `web/test_receptionist_role.mjs`
6. `backend/app/api/admin/recruitment.py`
7. `backend/app/services/recruitment.py`
8. `backend/app/models/recruitment.py` (`Candidate`, `CandidateOffer`)
9. `backend/app/models/__init__.py` (line 163 export)
10. `backend/app/core/permissions.py` (lines 146–150, 243–245, 285–287, 355–356)
11. `backend/app/core/modules.py` (line 38)
12. `backend/app/main.py` (lines 36, 69)
13. `backend/tests/test_teacher_leave_and_recruitment.py` (lines 257–377)

#### 3.2 Frontend Deletion Steps
1. In `web/src/screens.ts`:
   - Remove `"recruitment"` from `ModuleCode` union.
   - Remove `/recruitment` screen entry from `SCREENS` array.
2. Delete files:
   - `web/src/pages/RecruitmentPage.tsx`
   - `web/src/pages/RecruitmentPage.test.tsx`
   - `web/src/components/recruitment/PrintableApplicationForm.tsx` (and `web/src/components/recruitment/` directory).
3. In `web/src/screens.test.tsx` and `web/test_receptionist_role.mjs`:
   - Remove assertions verifying recruitment screen presence or receptionist recruitment intake.

#### 3.3 Backend Deletion Steps
1. Delete files:
   - `backend/app/api/admin/recruitment.py`
   - `backend/app/services/recruitment.py`
   - `backend/app/models/recruitment.py`
2. In `backend/app/models/__init__.py`:
   - Remove `from app.models.recruitment import Candidate, CandidateOffer`.
3. In `backend/app/main.py`:
   - Remove `from app.api.admin import recruitment as admin_recruitment`.
   - Remove `admin_recruitment.router` inclusion from routers list.
4. In `backend/app/core/permissions.py`:
   - Remove permissions:
     - `("recruitment.candidate.read", "View candidate applications")`
     - `("recruitment.candidate.write", "Create and edit candidate applications")`
     - `("recruitment.candidate.review", "Shortlist and reject candidate applications")`
     - `("recruitment.candidate.hire", "Issue job offers and confirm teacher hiring")`
   - Remove from `ADMIN_DEFAULT_PERMISSIONS`, `PRINCIPAL_PERMISSIONS`, and `RECEPTIONIST_DEFAULT_PERMISSIONS`.
5. In `backend/app/core/modules.py`:
   - Remove `Module("recruitment", "Teacher Recruitment", built=True, default_enabled=True)`.

#### 3.4 Database & Migrations Cleanup
- The migration `backend/alembic/versions/a1b2c3d4e5f6_teacher_leave_and_recruitment.py` created both `staff_leave_requests` / `substitutions` AND `candidates` / `candidate_offers`.
- **Safe Strategy:** Generate a new Alembic migration `drop_recruitment_tables` that cleanly executes `DROP TABLE IF EXISTS candidate_offers CASCADE;` and `DROP TABLE IF EXISTS candidates CASCADE;`.
- Down-revision remains `b2c3d4e5f6a7`. This preserves linear Alembic history and does not alter historical migration files.

#### 3.5 Test Suite Cleanup
- In `backend/tests/test_teacher_leave_and_recruitment.py`:
  - Rename file or keep as `backend/tests/test_teacher_leave.py`.
  - Remove recruitment tests:
    - `test_recruitment_candidate_intake_and_rbac`
    - `test_recruitment_admin_pipeline_offer_and_teacher_onboarding`
  - Ensure all 7 leave, substitution matrix, and 100% gate tests pass cleanly.

---

### TASK 4 — Global Replacement of "Close" Controls with Red X

#### 4.1 Web Application: Shared Modal Replacement
- **File:** [`web/src/components/ui.tsx`](file:///c:/Users/SHIVANSH/OneDrive/Documents/AGENTS/school-management-system/web/src/components/ui.tsx) (lines 135–137)
- **Current:**
  ```tsx
  <header className="flex items-center justify-between mb-4">
    <h2 className="font-semibold">{title}</h2>
    <button onClick={onClose} className="text-ink-faint hover:text-ink">
      Close
    </button>
  </header>
  ```
- **Replacement:**
  ```tsx
  <header className="flex items-center justify-between mb-4">
    <h2 className="font-semibold text-lg text-ink">{title}</h2>
    <button
      type="button"
      onClick={onClose}
      aria-label="Close"
      className="text-red-500 hover:text-red-700 hover:bg-red-50 p-1.5 rounded-full transition-colors flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-red-400"
    >
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </header>
  ```
- Because almost all modals (ConfirmDialog, DefaultersModal, GrievanceDetailModal, IntakeConfigModal, RunnerModal) consume `<Modal>`, this single change instantly standardizes dozens of dialogs across the web app.
- Audit standalone modals/drawers in `web/src/pages/` (e.g. `Dashboard.tsx`, `Reports.tsx`, `Applications.tsx`) to replace any custom `<button>Close</button>` in headers with the red SVG close icon.

#### 4.2 Mobile Application: Modal & Drawer Close Controls
- Audit all mobile modal components:
  1. `mobile/app/(teacher)/grievances.tsx` (lines 266, 305)
  2. `mobile/app/(teacher)/stock.tsx` (lines 310, 395)
  3. `mobile/app/(parent)/grievances.tsx` (lines 289, 330)
  4. `mobile/app/(parent)/attendance.tsx`
  5. `mobile/src/components/NavDrawer.tsx` (new hamburger drawer)
- **Replacement Pattern:**
  ```tsx
  <Pressable
    onPress={onClose}
    style={{
      padding: 6,
      borderRadius: 20,
      backgroundColor: "rgba(239, 68, 68, 0.1)",
      alignItems: "center",
      justifyContent: "center",
    }}
    hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
    accessibilityRole="button"
    accessibilityLabel="Close"
  >
    <Ionicons name="close" size={22} color="#ef4444" />
  </Pressable>
  ```
- Make sure close buttons have high contrast, red styling, adequate touch target (minimum 44×44px with hitSlop), and accessible labeling.

---

## 2. VERIFICATION & ACCEPTANCE CRITERIA

All 9 acceptance gates must pass before Session 9 can be marked complete:

| Gate | Verification Command | Expected Outcome |
|---|---|---|
| **Gate 1: Backend Test Suite** | `school-management-system/.venv/Scripts/python.exe -m pytest -q` | 100% green (all remaining tests pass, 0 regressions, ~729 passed after recruitment test purge) |
| **Gate 2: Web Test Suite** | `npm test` in `web/` | 100% green across all active test files |
| **Gate 3: Web Typecheck** | `npx tsc --noEmit` in `web/` | **0 errors** |
| **Gate 4: Mobile Typecheck** | `npx tsc --noEmit` in `mobile/` | **0 errors** |
| **Gate 5: Production Web Build** | `npm run build` in `web/` | Clean build with zero broken imports or route references |
| **Gate 6: Mobile 4 Bottom Tabs** | Inspect Parent, Teacher, Student layouts | Exactly 4 tabs on each role bottom bar: Parent (Home, Child, Fees, Profile), Teacher (Home, Classes, Attendance, Profile), Student (Home, Timetable, Homework, Profile) |
| **Gate 7: Mobile Hamburger Drawer** | Test top-left menu on all 3 roles | Opens smooth drawer with user profile, categorized sections (Academics, Operations, Communication, Other), full functionality preserved, red X close |
| **Gate 8: Dashboard Fee Chart Removed** | Inspect `web/src/pages/Dashboard.tsx` in browser | Fee Collection graph is completely absent, no empty white space, no broken layout |
| **Gate 9: Zero Recruitment References** | Grep `recruitment` across `web/src/`, `backend/app/`, `mobile/app/` | 0 active product references, obsolete files deleted, DB migration clean |

---

## 3. STEP-BY-STEP EXECUTION RUNBOOK FOR SESSION 9

Follow this sequence to execute Session 9 cleanly:

1. **Step 1: Website Fee Collection Chart Removal**
   - Edit `web/src/pages/Dashboard.tsx` to remove `<Card title="Fee Collection">` and clean up Recharts imports.
   - Run `npm test -- src/pages/Dashboard.test.tsx` in `web/` to verify dashboard unit tests.

2. **Step 2: Teacher Recruitment Deletion**
   - Remove recruitment permissions from `backend/app/core/permissions.py`.
   - Remove `"recruitment"` module from `backend/app/core/modules.py`.
   - Remove route and router from `backend/app/main.py`.
   - Delete `backend/app/api/admin/recruitment.py`, `backend/app/services/recruitment.py`, `backend/app/models/recruitment.py`.
   - Generate migration to drop `candidate_offers` and `candidates` tables.
   - Remove recruitment tests in `backend/tests/test_teacher_leave_and_recruitment.py`.
   - Delete frontend `RecruitmentPage.tsx`, `RecruitmentPage.test.tsx`, `components/recruitment/`, and `screens.ts` entry.
   - Verify backend tests: `.venv/Scripts/python.exe -m pytest -q`.
   - Verify web tests: `npm test` in `web/`.

3. **Step 3: Global Red-X Close Controls**
   - Update `Modal` in `web/src/components/ui.tsx` with red SVG X icon and `aria-label="Close"`.
   - Audit custom dialogs in `web/src/`.
   - Update mobile modals in `mobile/app/(parent)/`, `mobile/app/(teacher)/` with red `Ionicons name="close"`.

4. **Step 4: Mobile App Navigation Redesign**
   - Create `mobile/src/components/NavDrawer.tsx` with user header, grouped menu items, red X close, and logout action.
   - Refactor `mobile/app/(parent)/_layout.tsx` to 4 visible tabs + hamburger menu.
   - Refactor `mobile/app/(teacher)/_layout.tsx` to 4 visible tabs + hamburger menu.
   - Refactor `mobile/app/(student)/_layout.tsx` to 4 visible tabs + hamburger menu.
   - Run `npx tsc --noEmit` in `mobile/` to verify zero type errors.

5. **Step 5: Full Verification & Documentation Update**
   - Run full backend suite, web suite, and both typecheckers.
   - Update `SINGLE_SOURCE_OF_TRUTH.md`, `CLAUDE.md`, and `MEMORY.md`.
