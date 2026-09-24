# SESSION-HANDOFF-14: Transport Module Upgrade — Plan 1, Plan 2 & Address-Based Location System

> **Session Completed:** Session 14  
> **Status:** ALL DELIVERABLES COMPLETED & VERIFIED  
> **Branch:** `slice/office-feedback` (strictly local development; NEVER push to remote)  
> **Migration Head:** `f6a7b8c9d0e1` (`f6a7b8c9d0e1_route_stop_address.py`)  
> **Backend Test Baseline:** 749 passed, 1 skipped, 0 failed  
> **Web Test Baseline:** 109 passed across 20 test files, 2 skipped  
> **Web Typecheck Baseline:** 0 errors (`npx tsc --noEmit` in `web/`)  
> **Mobile Typecheck Baseline:** 0 errors (`npx tsc --noEmit` in `mobile/`)  
> **Visual Verification Suite:** 25/25 passed (`node verify_transport_upgrade_visual.mjs` in `web/`)  
> **Corpus Root:** `c:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system`  

---

## 1. COMPLETED DELIVERABLES IN SESSION 14

### 1. Address-First Location System
- **Core Architecture:**
  - Shifted transport workflow from manual coordinate entry to a human-readable address-first approach.
  - Normal users search or input a physical address (e.g. `Vibhuti Khand, Gomti Nagar, Lucknow`); coordinates `(latitude, longitude)` are resolved automatically in the background.
  - Coordinates are stored internally in the database to power maps, proximity calculations, and future GPS tracking without exposing raw lat/lon entry to end-users.
- **Geocoding Engine (`backend/app/services/geocoding.py`):**
  - High-precision Lucknow landmark cache (Vibhuti Khand, Patrakarpuram, Polytechnic, Hazratganj, Alambagh, Krishna Nagar, Charbagh, Indira Nagar, etc.).
  - Deterministic hash-based geocoding fallback for unlisted addresses ensuring reproducible coordinate assignment.
  - Haversine distance calculator calculating great-circle distance in kilometers between student addresses and route stops.
- **Database Schema Migration (`f6a7b8c9d0e1`):**
  - Added nullable `address` column to `route_stops` table with Alembic upgrade/downgrade scripts.

### 2. Plan 1: Fleet & Route Setup Desk
- **Vehicle Fleet Management (`web/src/pages/transport/VehicleModal.tsx`):**
  - Full CRUD operations for school vehicles.
  - Ownership options: `owned` vs. `hired`.
  - Vehicle status: `active`, `under_maintenance`, `grounded`.
  - GPS device ID tracker field.
  - Seating capacity guard: backend and frontend prevent reducing vehicle seating capacity below the number of currently active assigned riders on its route.
- **Route & Stop Builder (`web/src/pages/transport/RouteBuilderModal.tsx`):**
  - Interactive route builder modal supporting route code, name, and total route distance in km.
  - Stop sequence builder with move-up, move-down, add, and remove controls.
  - Address-first stop inputs: stop name, address, landmark, pickup time, drop time, and fee slab link.
  - One-click "Resolve 📍" button triggering immediate geocoding feedback for each stop.
- **Crew & Vehicle Dispatch Desk (`web/src/pages/transport/CrewDispatchModal.tsx`):**
  - Unified dispatch modal to assign a bus, designated driver, and attendant to a route.
  - Live compliance badges: driving license verification status and police verification check for drivers and attendants.
  - Contact phone numbers displayed for rapid emergency communication.
- **Distance Fee Slabs Management (`web/src/pages/transport/SlabsModal.tsx`):**
  - Slabs CRUD table linked to stops for monthly transport billing tiers (e.g., 0-5 km @ ₹800/mo, 5-10 km @ ₹1100/mo, 10-15 km @ ₹1500/mo).

### 3. Plan 2: Student Transport Allocation Desk
- **Admission Transport Queue:**
  - Automatically identifies enrolled students whose application indicated a requirement for school transport.
  - Provides a one-click direct allocation workflow.
- **Student Search & Proximity Stop Allocation:**
  - Dedicated search endpoint (`/admin/transport/students/search`) allowing Transport In-Charge to locate any enrolled student by name or admission number without granting broad People module permissions (`students.profile.read`).
  - Proximity stop ranking (`/admin/transport/stops/nearby`): ranks all active route stops by Haversine distance from the student's address, showing seats occupied vs. available.
  - One-click assignment with pickup/drop direction selector.
- **Active Riders & Route Transfers:**
  - Comprehensive list of active riders with route, stop, pickup/drop times, and parent contact.
  - Transfer Stop workflow requiring a mandatory justification reason.
  - Service termination workflow with confirmation and mandatory cancellation reason.
- **Printable A4 Route Manifest & Roster (`web/src/pages/PrintableRouteRoster.tsx`):**
  - Formal school letterhead (`SUNRISE PUBLIC SCHOOL`) with CBSE affiliation details.
  - Route header with vehicle registration, driver contact, and attendant contact.
  - Stop-by-stop breakdown with scheduled pickup/drop timings and student manifests.
  - Student details including admission number, class-section, ride direction, parent emergency contact numbers, and authorized pickup escorts with relationship.
  - Standard `window.print()` trigger with print-friendly CSS hiding UI navigation and buttons.

### 4. RBAC Hardening & Security
- **Strict Role Boundaries:**
  - `transport_incharge` system role remains strictly isolated with zero access to People (`students.profile.read`, `teachers.*`) and Academics (`academics.*`).
  - All transport data requirements (student search, class labels, fee slabs, crew contacts) are served through hardened `/admin/transport/*` endpoints enforcing `transport.setup.*` and `transport.assignment.*` permissions.

---

## 2. VERIFIED TEST BASELINES

| Test Suite | Result | Details |
| :--- | :--- | :--- |
| **Backend Pytest** | **749 passed, 1 skipped, 0 failed** | Full backend test suite passing (`.venv/Scripts/python -m pytest -q`) |
| **Transport Unit Tests** | **50 passed, 1 skipped, 0 failed** | `test_transport.py`, `test_transport_upgrade.py`, `test_transport_incharge_rbac.py` |
| **Frontend Web Tests** | **109 passed, 2 skipped across 20 files** | `npm test` in `web/` |
| **Frontend Web Typecheck** | **0 errors** | `npx tsc --noEmit` in `web/` |
| **Mobile App Typecheck** | **0 errors** | `npx tsc --noEmit` in `mobile/` |
| **Puppeteer Visual Suite** | **25/25 passed** | `node verify_transport_upgrade_visual.mjs` in `web/` |

---

## 3. VISUAL VERIFICATION ARTIFACTS

All visual screenshots captured and saved to `docs/screenshots/` and system artifact store:
- `proof_transport_upgrade_main_desk.png`: Main Transport Desk with stats, route operations, fleet table, compliance, and action buttons.
- `proof_transport_printable_roster.png`: Printable A4 Route Manifest & Roster with school header, crew details, student manifests, and authorized escorts.
- `proof_transport_crew_dispatch.png`: Crew & Vehicle Dispatch modal with driver/attendant dropdowns and verification badges.
- `proof_transport_route_stop_builder.png`: Route & Stop Builder with address-first resolution and timing controls.
- `proof_transport_student_allocation_desk.png`: Student Transport Allocation Desk with admission queue tab.
- `proof_transport_student_search_tab.png`: Student Search & Allocation tab with proximity-ranked stop assignment.
- `proof_transport_fee_slabs.png`: Distance Fee Slabs management desk with monthly fee tiers.

---

## 4. ARCHITECTURAL DECISIONS & INVARIANTS

1. **Address-First, Coordinate-Backed:** Normal users only interact with human-readable addresses; coordinates are automatically geocoded and saved behind the scenes for maps, distance calculations, and future GPS.
2. **Capacity Invariant:** A vehicle's capacity cannot be decreased below the number of students currently actively assigned to that route.
3. **Mandatory Audit Reasons:** Route transfers and transport service terminations strictly require non-empty text justification for audit tracking.
4. **Isolated Transport Queries:** Transport In-Charge queries students and classes only via dedicated transport endpoints; core student management endpoints return HTTP 403 Forbidden.
