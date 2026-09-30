# SESSION-HANDOFF-17: Expo Mobile App Login Fix, Dynamic Network Architecture & Multi-Role Demo Authentication

> **Session Completed:** Session 17  
> **Status:** ALL SESSION 17 DELIVERABLES COMPLETED & VERIFIED  
> **Branch:** `slice/office-feedback` (synced with `origin/main`)  
> **Backend Test Baseline:** 749 passed, 1 skipped, 0 failed (`../.venv/Scripts/python.exe -m pytest -q`)  
> **Backend RBAC Baseline:** 13 passed, 0 failed (`pytest tests/test_rbac.py`)  
> **Backend Auth Baseline:** 8 passed, 0 failed (`pytest tests/test_auth.py`)  
> **Web Test Baseline:** 109 passed, 2 skipped across 20 test files (`npm test` in `web/`)  
> **Web Typecheck Baseline:** 0 errors (`npx tsc --noEmit` in `web/`)  
> **Mobile Typecheck Baseline:** 0 errors (`npx tsc --noEmit` in `mobile/`)  
> **Live Deployments:**  
> - Frontend: `https://school-management-system-blush-iota.vercel.app` (Vercel)  
> - Backend: `https://school-management-system-12ks.onrender.com` (Render, `/healthz` 200 OK)  
> - Database: Neon Tech Serverless PostgreSQL  
> **Corpus Root:** `c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`  

---

## 1. COMPLETED DELIVERABLES IN SESSION 17

### 1. Root Cause Resolution for Infinite "Signing in..." State
- **Root Cause Identified:** React Native's native `fetch()` implementation has no default request timeout. When the app attempted to contact an unreachable IP (`192.168.29.227:8000` from an older Wi-Fi network), the promise hung indefinitely. Consequently, `await login(...)` never resolved or rejected, leaving the submit handler stuck with `busy === true` ("Signing in...").
- **15-Second `AbortController` Timeout (`mobile/src/api/client.ts`):**
  - Integrated `AbortController` with a 15-second timer into `request<T>()`.
  - Catches `AbortError` and produces clean, actionable error messages: `"Request timed out — could not reach <URL>. Is the backend running?"`
  - Catches general network failures (DNS, unreachable host, connection refused) and surfaces `"Network error — could not connect to <URL>. Check that the backend is running and reachable."`
  - The `finally { setBusy(false) }` block now reliably executes in all success, failure, timeout, and unexpected error states.

### 2. Dynamic Packager Host Discovery & Cloud Fallback Architecture
- **Stale IP Override Elimination:**
  - Previously, `resolveApiBaseUrl()` returned any non-loopback `EXPO_PUBLIC_API_URL` before evaluating `Constants.expoConfig?.hostUri`.
  - When the developer's Wi-Fi network changed to `10.109.197.170`, the hardcoded `192.168.29.227` in `mobile/.env` intercepted and prevented dynamic discovery.
- **Improved Resolution Hierarchy (`mobile/src/api/client.ts`):**
  1. `https://` Cloud URLs: Always respected (e.g. Render production/staging).
  2. Web Platform: Uses explicit env or `window.location.hostname:8000`.
  3. Dynamic Expo Packager Host (`Constants.expoConfig?.hostUri`): In development with Expo Go or dev client, extracts the exact IP that served the JS bundle to the device (`10.109.197.170`). This is guaranteed reachable by the device.
  4. Custom LAN / Emulator overrides if provided.
  5. Android Emulator loopback alias (`10.0.2.2:8000`).
  6. Resilient Cloud Fallback (`https://school-management-system-12ks.onrender.com`): Physical devices running outside the local network will automatically connect to the live cloud backend rather than hanging on a dead loopback (`127.0.0.1`).
- **Environment & Server Configuration:**
  - `mobile/.env` updated to active LAN IP: `EXPO_PUBLIC_API_URL=http://10.109.197.170:8000`.
  - Local backend uvicorn started with `--host 0.0.0.0 --port 8000` to allow inbound connections from physical mobile devices on the Wi-Fi LAN.

### 3. Imperative Router Navigation & Demo Authentication UX
- **Imperative Navigation (`mobile/app/index.tsx`):**
  - Replaced purely declarative `<Redirect>` render with an explicit `router.replace(`/(${role})/dashboard`)` call immediately after `await login(...)` succeeds.
  - Retained `if (me) return <Redirect ... />` for initial app load when already authenticated.
- **Tap-to-Fill Demo Credentials (`mobile/app/index.tsx`):**
  - Documented role-specific demo passwords from `backend/seed.py`:
    - **Student:** `2024000001` / `Student@123`
    - **Parent:** `9876500001` / `Parent@123`
    - **Teacher:** `TCH001` / `Teacher@123`
  - Added an "Auto-fill demo password" button under the password input.
  - Interactive Demo Accounts section: Tapping any role row (Student, Parent, Teacher) automatically selects the role tab, fills the login ID, and enters the correct demo password.

### 4. RBAC Auto-Heal Scoping Precision
- **Bug Fixed in `backend/app/services/rbac.py`:**
  - Session 16 added an auto-heal fallback that granted `super_admin` role to any user with `user.role == UserRole.admin` having 0 role assignments (fixing the cloud `--skip-wipe` seed bug).
  - This broad check caused unit tests testing unassigned accounts (`nobody@sunrisepublic.edu`) and segregation of duties (`cashier@sunrisepublic.edu`) to fail because they were granted full super_admin permissions.
  - Refined the check to strictly scope auto-healing to primary school admin accounts: `user.login_id.startswith("admin@") or user.login_id == "admin"`.
  - Verified: All 13/13 tests in `tests/test_rbac.py` and 8/8 tests in `tests/test_auth.py` pass.

### 5. Interactive Expo QR Code Desk & Connection Widget
- Generated a high-resolution 592x592 QR code PNG encoding `exp://10.109.197.170:8081` with high error correction.
- Created standalone interactive widget `expo_qr_widget.html` in artifact store with embedded base64 QR image, one-click manual URL copy, and live demo credentials reference.

---

## 2. FILES MODIFIED IN SESSION 17

| File | Changes Made |
| :--- | :--- |
| `mobile/src/api/client.ts` | 15s `AbortController` timeout on all fetch requests; prioritized Expo packager `hostUri` dynamic discovery; resilient cloud fallback to Render. |
| `mobile/src/auth/AuthContext.tsx` | Wrapped `/auth/me` call in try/catch to clear saved token and re-throw on error, preventing orphan token states. |
| `mobile/app/index.tsx` | Added `useRouter()` and imperative `router.replace` navigation; added role-specific demo passwords and tap-to-fill UI. |
| `mobile/.env` | Updated `EXPO_PUBLIC_API_URL=http://10.109.197.170:8000`. |
| `backend/app/services/rbac.py` | Refined auto-heal check in `grants_for()` to `(user.login_id.startswith("admin@") or user.login_id == "admin")`. |
| `SINGLE_SOURCE_OF_TRUTH.md` | Updated to Session 17 with cloud deployment URLs, verified baselines, and mobile authentication specs. |
| `CLAUDE.md` | Updated to Session 17 handoff reference, live cloud deployment URLs, and test baselines. |
| `MEMORY.md` | Updated executive summary, milestone status, and added Traps 18, 19, and 20. |

---

## 3. VERIFIED TEST BASELINES

```bash
# Backend full test suite (749 passed, 1 skipped, 0 failed)
cd backend && ../.venv/Scripts/python.exe -m pytest -q

# Backend RBAC test suite (13 passed, 0 failed)
cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_rbac.py -v

# Backend Auth test suite (8 passed, 0 failed)
cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_auth.py -v

# Web unit test suite (109 passed, 2 skipped across 20 files)
cd web && npm test

# Web TypeScript compilation (0 errors)
cd web && npx tsc --noEmit

# Mobile TypeScript compilation (0 errors)
cd mobile && npx tsc --noEmit
```

---

## 4. UPCOMING SCOPE FOR SESSION 18

The following five major feature requirements have been defined for **Session 18**:

### 1. Website — Admin
- **Remove Teacher Meeting Slip:**
  - Completely remove **Teacher Meeting Slip** from the front desk reception suite.
  - Retain **Principal Meeting Slip**.
  - Remove related UI, routes, APIs, permissions, notifications, and dead code without breaking Principal Meeting Slip workflows.
- **Admin User Access Management (Mobile Users):**
  - Authorized Admin users can manage mobile app access for **Teachers, Parents, and Students**.
  - **Block / Unblock:** Enforced at backend/authentication level. A blocked user cannot authenticate, and existing tokens/sessions must be invalidated/rejected.
  - **Password Reset / Change:** Admin can securely reset or change password for any teacher, parent, or student. No plaintext exposure. Invalidate existing sessions upon reset.
  - Add clear user-management UI displaying active vs. blocked access status.

### 2. Mobile App — Timetable
- Investigate and resolve the broken Timetable section across all three roles:
  - **Teacher:** Weekly teaching slots and subject schedule.
  - **Parent:** Selected child's class timetable schedule.
  - **Student:** Class timetable schedule.
- Trace and fix: database seed/queries, backend API endpoints, tenant scoping, data mapping, and mobile UI rendering.

### 3. Mobile App — Menu (Drawer Navigation)
- Ensure every feature currently accessible via the 4 bottom tabs is **ALSO** available in the main drawer Menu (`NavDrawer.tsx`) for **Teacher, Parent, and Student**.
- Both navigation paths (bottom tabs and drawer items) must route to the same underlying screens without duplicating code or violating role permissions.

### 4. Teacher Leave System Enhancement
- **Configurable Leave Types:** Support configurable leave types (e.g. CL, Medical, Earned) rather than hard-coding around CL.
- **CL (Casual Leave) Auto-Period Inspection:**
  - Selecting single date or date range automatically inspects teacher's timetable to identify every affected class/period on every affected day.
  - Teacher must arrange substitution for each affected period.
- **Ranked Substitute Suggestions:**
  - Find eligible available teachers (no class in that period, not already substituting, not absent, active).
  - Priority ranking:
    1. Highest priority: Matches BOTH same subject AND same class/grade.
    2. Matches same subject.
    3. Matches same class/grade.
    4. Other eligible available teachers.
- **Substitution Acceptance Workflow:**
  - Requesting teacher selects substitute → Substitute receives notification → Substitute can Accept or Reject.
  - If rejected, requester selects another substitute.
  - Clear substitution status per period (e.g. `29 Sept — Period 1 — Class 8A — Mathematics — Rahul — Accepted ✓`).
  - CL application requires 100% confirmed substitutions before final arrangement.
- **Other Leave Types (Non-CL):**
  - Teacher submits request without arranging substitutes; Admin becomes responsible for arranging substitutions via existing admin workflow.

### 5. Parent App — Multiple Languages (i18n)
- Proper internationalization for the **Parent mobile app**.
- Initial languages: **English** and **Hindi**.
- Settings location: **Parent → Profile / Settings → Language**.
- Persistent language selection on device.
- Key-based translation resource architecture (e.g. `attendance.title` -> `Attendance` / `उपस्थिति`).
- Dynamic content (homework text, notices, student names) remains untranslated; static UI strings translated.
- Lightweight implementation without storing static strings in PostgreSQL.

---

## 5. REPOSITORY STATE
- **Branch:** `slice/office-feedback` (synced with `origin/main`)
- **Git Status:** Clean baseline, all tests green, live cloud verified.
