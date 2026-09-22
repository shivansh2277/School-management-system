# Packet 1 — Admission

Branch `slice/office-feedback`, off `slice/packet-0`, off `main` at `232a791`.
Nothing pushed, nothing merged. All work built and verified locally on the local Git branch.

---

## Executive Summary

Packet 1 delivers the end-to-end **Admission & Student Onboarding** pipeline for the Sunrise School ERP, fulfilling ERP Blueprint §5.1.

Prior to Packet 1, the backend had 41 FastAPI admission endpoints registered under `/admin/admission` with comprehensive model logic and test coverage, but zero frontend UI. Now, all 6 admission screens are fully implemented in the web client, registered in `web/src/screens.ts`, gated by granular RBAC permissions and module flags, and verified via automated test suites and real Chrome CDP browser interactions against a live running PostgreSQL database.

---

## What I Built

| Route | Screen Name | What a clerk does on it | Endpoints Used |
|---|---|---|---|
| `/admission` | **Admission overview** | Admission cycle switcher, high-level conversion funnel, seat utilization & quota by class, seat config modal, today's tests & interview schedule. | `GET /admin/admission/cycles`, `POST /admin/admission/cycles`, `PUT /admin/admission/cycles/{id}`, `GET /admin/admission/cycles/{id}/dashboard`, `GET /admin/admission/cycles/{id}/seats`, `PUT /admin/admission/cycles/{id}/classes` |
| `/admission/enquiries` | **Enquiries** | Log walk-in and phone enquiries, record follow-up interactions (calls, tours, WhatsApp), view full chronological interaction timeline, convert enquiry to draft application, mark invalid with typed audit reason. | `GET /admin/admission/enquiries`, `POST /admin/admission/enquiries`, `GET /admin/admission/enquiries/{id}`, `POST /admin/admission/enquiries/{id}/interactions`, `POST /admin/admission/enquiries/{id}/invalid` |
| `/admission/applications` | **Applications** | 360° applicant dossier management across 7 operational tabs: Biodata & Academics, Guardians & Siblings, Documents Checklist & Scrutiny, Written Tests & Interviews, Decisions & Offers, Offline Fees & Student Conversion, and Isolated Medical Info. | `GET/POST /admin/admission/applications`, `GET /admin/admission/applications/{id}`, `PUT .../guardians`, `PUT .../siblings`, `POST .../submit`, `POST .../verify-claims`, `GET/POST .../documents`, `POST .../documents/{code}/verify`, `GET .../evaluation`, `POST .../assessments`, `POST .../interviews`, `GET/POST .../decision`, `GET/POST .../offers`, `GET/POST .../fees`, `POST .../fees/{id}/void`, `GET .../conversion-preview`, `POST .../convert`, `GET/PUT .../medical` |
| `/admission/merit` | **Merit & selection** | Ranked merit list per class with test marks, interview panel scores, and verified claims. Batch decision action (Admit / Waitlist / Reject selected) with shared audit reason and seat category assignment. | `GET /admin/admission/cycles/{id}/merit`, `POST /admin/admission/cycles/{id}/decisions`, `POST /admin/admission/applications/{id}/decision` |
| `/admission/waitlist` | **Waitlist** | Ranked waitlist queue per class with seat availability gauges. "Promote next candidate" action with confirmation modal when lapsed offers or expanded quotas free up seats. | `GET /admin/admission/cycles/{id}/waitlist`, `GET /admin/admission/cycles/{id}/seats`, `POST /admin/admission/cycles/{id}/waitlist/promote` |
| `/admission/reports` | **Admission reports** | Real-time analytics computed on read: funnel drop-off rates, lead source attribution yield %, seat utilization table per class, demographics (gender & caste), rejection reasons breakdown, pipeline velocity (median days to decision & enrolment). | `GET /admin/admission/cycles/{id}/reports` |

---

## The `screens.ts` Entries

All six screens are registered under group `"Admission"` in `web/src/screens.ts`. Every permission was read directly from the backend router `app/routers/admin/admission.py`.

```ts
  {
    path: "/admission",
    label: "Admission overview",
    group: "Admission",
    permissions: ["admission.application.read"],
    modules: ["admission"],
  },
  {
    path: "/admission/enquiries",
    label: "Enquiries",
    group: "Admission",
    permissions: ["admission.enquiry.read"],
    modules: ["admission"],
  },
  {
    path: "/admission/applications",
    label: "Applications",
    group: "Admission",
    permissions: ["admission.application.read"],
    modules: ["admission"],
  },
  {
    path: "/admission/merit",
    label: "Merit & selection",
    group: "Admission",
    permissions: ["admission.application.read"],
    modules: ["admission"],
  },
  {
    path: "/admission/waitlist",
    label: "Waitlist",
    group: "Admission",
    permissions: ["admission.application.read"],
    modules: ["admission"],
  },
  {
    path: "/admission/reports",
    label: "Admission reports",
    group: "Admission",
    permissions: ["admission.application.read"],
    modules: ["admission"],
  },
```

---

## Domain Rules & Enforced Constraints

1. **An applicant is NEVER a student or user before conversion**:
   - Out of hundreds of enquiries and applications, only admitted families who pay admission fees matriculate.
   - Applications stay completely isolated in `applications`, `application_guardians`, `application_documents`, and `application_assessments`.
   - Only atomic `POST /admin/admission/applications/{id}/convert` creates official records in `students`, `student_enrolments`, and user logins.
2. **Sibling and Staff Claims are Claims, Not Facts**:
   - Sibling links and staff ward selections remain unverified flags (`CLAIM PENDING VERIFICATION`) until an office clerk clicks **Verify claims**, which checks the backend against active roster students.
3. **Mandatory Audit Reasons for Pipeline Moves**:
   - Marking an enquiry invalid (`POST .../invalid`) requires a typed reason.
   - Making an admission decision (`POST .../decision` - admitted, waitlisted, rejected) requires a non-empty typed reason stored in `audit_log`.
   - Voiding an admission fee receipt requires a typed reason.
4. **Isolated Medical Information (§15 Compliance)**:
   - Medical conditions, blood group, allergies, medications, and emergency treatment consents are sensitive health records.
   - Gated strictly behind `<Can permission="admission.medical.read">`, hiding tab contents from general reception clerks who hold only `admission.application.read`.
5. **Seat Quotas and Offer Expiry**:
   - Each class configures total capacity, general seats, and reserved quotas (e.g. RTE, Staff).
   - Issued offer letters have an expiration date (`expires_on`). When an offer lapses, seats release automatically, enabling waitlist candidate promotion.

---

## Verification — Commands and Their Real Output

All checks were run locally against native PostgreSQL `sunrise_test` and Vite web dev server:

### 1. TypeScript Strict Type-Checking
```
$ cd web && npx tsc --noEmit
(no output, exit code 0)
```

### 2. Frontend Unit & Permission Tests
```
$ cd web && npm test
 ✓ src/screens.test.tsx (20 tests)
 ✓ src/layout/Shell.test.tsx (5 tests)
 ✓ src/pages/Dashboard.test.tsx (4 tests | 2 skipped)
 ✓ src/App.test.tsx (3 tests)
 ✓ src/pages/Notices.test.tsx (2 tests)
 ✓ src/components/Can.test.tsx (6 tests)
 ✓ src/pages/admission/admission.test.tsx (4 tests)
 ✓ src/components/ConfirmDialog.test.tsx (4 tests)
 ✓ src/screens.permissions.test.ts (2 tests)
 ✓ src/api/client.types.test.ts (1 test)
 ✓ src/api/client.test.ts (6 tests)
 ✓ src/components/ui.test.tsx (4 tests)
 ✓ src/auth/AuthContext.test.tsx (1 test)
 ✓ src/api/errors.test.ts (2 tests)

 Test Files  14 passed (14)
      Tests  62 passed | 2 skipped (64)
   Duration  10.27s
```

### 3. OpenAPI Schema Drift
```
$ cd web && npm run api:check
> node scripts/generate-api-types.mjs --check
schema.d.ts is up to date
```

### 4. Vite Production Build
```
$ cd web && npm run build
vite v5.4.21 building for production...
✓ 916 modules transformed.
dist/assets/Waitlist-HsUnfRdq.js             4.67 kB │ gzip:   1.87 kB
dist/assets/AdmissionReports-Bj0Z1819.js     6.89 kB │ gzip:   2.12 kB
dist/assets/MeritSelection-9lC-ifE4.js      10.97 kB │ gzip:   3.07 kB
dist/assets/Enquiries-BOtkNOfg.js           14.39 kB │ gzip:   4.15 kB
dist/assets/AdmissionOverview-C18l0Yz4.js   16.84 kB │ gzip:   4.26 kB
dist/assets/Applications-CurNdDpS.js        66.35 kB │ gzip:  13.35 kB
✓ built in 5.64s
```

### 5. Multi-Role Live API Smoke
```
$ cd web && node smoke.mjs http://127.0.0.1:8078
== admin
  [PASS] Admission overview -> /admin/admission/cycles — 200
  [PASS] Enquiries -> /admin/admission/enquiries — 200
  [PASS] Applications -> /admin/admission/applications — 200
  [PASS] Merit & selection -> /admin/admission/cycles — 200
  [PASS] Waitlist -> /admin/admission/cycles — 200
  [PASS] Admission reports -> /admin/admission/cycles — 200

== fee counter
  [PASS] Admission overview -> /admin/admission/cycles — 403
  [PASS] Enquiries -> /admin/admission/enquiries — 403
  [PASS] Applications -> /admin/admission/applications — 403
  [PASS] Merit & selection -> /admin/admission/cycles — 403
  [PASS] Waitlist -> /admin/admission/cycles — 403
  [PASS] Admission reports -> /admin/admission/cycles — 403

== transport manager
  [PASS] Admission overview -> /admin/admission/cycles — 403
  [PASS] Enquiries -> /admin/admission/enquiries — 403
  [PASS] Applications -> /admin/admission/applications — 403
  [PASS] Merit & selection -> /admin/admission/cycles — 403
  [PASS] Waitlist -> /admin/admission/cycles — 403
  [PASS] Admission reports -> /admin/admission/cycles — 403

All smoke checks passed
```

### 6. Backend Test Suite
```
$ cd backend && ../.venv/Scripts/python.exe -m pytest -q
631 passed, 1 skipped, 53 warnings in 295.29s (0:04:55)
```

---

## Live Browser Verification Proofs (Chrome CDP)

Executed via automated headless Chrome CDP runner (`scratch/run_admission_demo.mjs`) on `http://localhost:5173`:

| Step | Action & Verification | Screenshot Captured |
|---|---|---|
| **01** | Admission Overview: Funnel progression steps, intake capacity, cycle switcher | `01_admission_overview.png` |
| **02** | Configure Seat Capacity Modal: Class name, stream, total seats, RTE/Staff quota, age limits | `02_admission_configure_seats_modal.png` |
| **03** | Enquiry Register: Walk-in inquiry list, mobile numbers, channel pills, due dates | `03_enquiries_register.png` |
| **04** | Enquiry Details Drawer: Full contact info, child DOB, start application action | `04_enquiry_created_and_drawer.png` |
| **05** | Enquiry Interaction Logged: Chronological timeline entry with outcome and notes | `05_enquiry_interaction_logged.png` |
| **06** | Applications Master Register: Search bar, status filters, category badges, 360° Profile action | `06_applications_register.png` |
| **07** | 360° Dossier Tab 1 (Biodata & Academic): Completeness bar, address, past schooling | `07_app_360_overview_tab.png` |
| **08** | 360° Dossier Tab 2 (Guardians & Siblings): Primary guardian flag, sibling link, "Verify claims" | `08_app_guardians_and_claims.png` |
| **09** | 360° Dossier Tab 3 (Documents Checklist): Mandatory checklist, upload trigger, physical original verification | `09_app_documents_checklist.png` |
| **10** | 360° Dossier Tab 4 (Evaluation & Scoring): Schedule written exam, absent toggle, interview rating | `10_app_evaluation_scoring.png` |
| **11** | 360° Dossier Tab 5 (Decision & Offers): Committee decision audit trail, issue offer letter, expiry date | `11_app_decision_and_offers.png` |
| **12** | 360° Dossier Tab 6 (Fees & Student Conversion): Offline receipt generation, readiness inspection, atomic convert | `12_app_fees_and_conversion_preview.png` |
| **13** | 360° Dossier Tab 7 (Medical Records): Blood group, allergies, emergency doctor, treatment consent | `13_app_medical_record_gated.png` |
| **14** | Merit Ranking & Selection: Class quota banner, ranked applicant list, batch decision checkboxes | `14_merit_selection.png` |
| **15** | Waitlist Queue: Waiting list order, current seats open gauge, promote next candidate button | `15_waitlist_queue.png` |
| **16** | Admission Reports: Funnel drop-off analytics, source attribution yield %, class seat utilization | `16_admission_reports.png` |
| **17** | Role Refusal Negative Test: Fee Counter logs in, Admission menu absent from sidebar, direct URL refused | `17_fee_counter_refused.png` |

---

## Unified Leadership Logins Reference

Per owner directive, all school leadership can log in with either the shared administrator ID or individual title-based addresses, sharing the same password:

- **Password (All Leadership)**: `Admin@123`
- **Shared Leadership Login**: `admin@sunrisepublic.edu`
- **Principal**: `principal@sunrisepublic.edu`
- **Vice Principal**: `viceprincipal@sunrisepublic.edu`
- **Owner / Management**: `owner@sunrisepublic.edu`
- **Academic Coordinator**: `coordinator@sunrisepublic.edu`
