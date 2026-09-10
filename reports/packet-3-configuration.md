# Packet 3 — Configuration

Branch `slice/office-feedback`, on top of `2fff2ae`. **Nothing committed, nothing
pushed, no PR.** The work is in the working tree for the orchestrator to review.

---

## What I built

| Route | What a clerk does there | Endpoints it calls |
|---|---|---|
| `/configuration` | One screen, three cards. **Modules** — turn a module on or off, each row saying in plain English what stops working. **Settings** — the whole registry, grouped by area (late fee, sibling concession, fees, attendance, examinations, teacher workload, communication, school), edited and saved together. **Custom fields** — the school's own attributes per entity, added and retired. | `GET /admin/configuration`, `PUT /admin/configuration`, `GET /admin/custom-fields`, `POST /admin/custom-fields`, `DELETE /admin/custom-fields/{id}` |

Enabling a module no longer needs a `curl`, which is what ERP_BLUEPRINT §0.18
asked for.

Three things about the screen that are decisions, not accidents:

- **Nothing hardcodes a setting key.** The GET returns the registry definitions
  beside the values, so the form is built from them: a new `SettingDef` in
  `core/settings_registry.py` appears on this screen with no frontend change.
  The area labels are presentation only, matched on key prefix, and an
  unmatched key still renders under "Other".
- **A module switch refreshes `/auth/me`.** The API honours the switch at once,
  but the sidebar is drawn from the cached `modules` list, so without this the
  clerk turns Transport off, sees the menu unchanged and concludes the switch is
  broken. `AuthContext` gained a `refresh()` for it. **Verified in the browser:**
  turning HR on made "Staff" appear in the sidebar without a reload, and turning
  it back off removed it.
- **Int settings are validated in the browser.** Typing `12.5` into "Per day"
  puts *A whole number* under the input and disables Save, rather than sending it
  and getting back a 422 the clerk cannot act on. Confirmed by clicking.

### Also fixed: `PATCH /admin/settings` always 422'd

`GET /admin/settings` returns `academic_year`; the PATCH model was
`extra="forbid"`; the Settings page posts the whole GET body back. So **Save on
`/settings` had never once worked** — pre-existing on `main`.

`api/admin/stats.py::SettingsUpdate` now declares `academic_year` and the handler
excludes it from the write (the year is an `AcademicYear` row, not a school
column). `extra="forbid"` stays, so an unknown field is still refused — that was
a deliberate earlier fix and this does not undo it.

Pinned by two tests in `backend/tests/test_stats.py`:
`test_settings_accepts_its_own_get_body_back` and
`test_settings_still_refuses_an_unknown_field`. **Proven to fail without the
fix** — output below.

`web/src/pages/Settings.tsx` now renders the academic-year input disabled with
a `title` explaining why. An input that looks editable and is silently ignored
is the same lie as the 422 it replaced.

---

## The `screens.ts` entry the orchestrator must add

Already applied in the working tree (`web/src/screens.ts`, inserted immediately
before the `/settings` entry). Verbatim:

```ts
  {
    path: "/configuration",
    label: "Configuration",
    group: "Administration",
    // GET /admin/configuration and GET /admin/custom-fields - both
    // api/admin/settings.py, both on the module-level `reader` =
    // require_permission("admin.settings.read", school_wide=True), neither
    // behind a module gate. The writes (PUT /admin/configuration, POST and
    // DELETE /admin/custom-fields) need admin.settings.write and are excluded
    // per the note above: they gate themselves on their own controls, and
    // declaring the write permission here would hide the module switches from
    // a read-only auditor who is meant to be able to see them.
    //
    // No module is declared on purpose. This is the screen that turns modules
    // on, so gating it on one is how a school locks itself out of its own
    // configuration.
    permissions: ["admin.settings.read"],
    element: lazy(() =>
      import("./pages/Configuration").then((m) => ({ default: m.Configuration })),
    ),
  },
```

**Which router I read to determine each permission:** `backend/app/api/admin/settings.py`.
All five endpoints on that router take `reader = require_permission("admin.settings.read",
school_wide=True)` as their user dependency; the three writes additionally carry
`writer = Depends(require_permission("admin.settings.write"))`. Neither
`GET /admin/configuration` nor `GET /admin/custom-fields` has a
`module_enabled(...)` dependency, so no module is declared. The write permission
`admin.settings.write` appears on the controls (`ActionButton`), not in the
registry entry — declaring it here would hide the screen from a read-only role.

Two tests were added to `web/src/screens.test.tsx` pinning that the screen shows
on `admin.settings.read` with **no modules enabled at all** (the state a fresh
tenant, or one accidental "turn off", is in) and stays hidden from a fee
collector.

---

## Verification — commands and their real output

Baseline at `2fff2ae`, **before** any change, confirmed green:

```
$ cd backend && ../.venv/Scripts/python.exe -m pytest -q
626 passed, 53 warnings in 118.45s (0:01:58)

$ cd web && npx tsc --noEmit
TSC OK                      (no output; 0 errors)

$ npm test
 Test Files  12 passed (12)
      Tests  45 passed (45)

$ npm run api:check
schema.d.ts is up to date

$ npm run build
✓ built in 4.18s

$ SMOKE_PASSWORD='Admin@123' node smoke.mjs http://127.0.0.1:8078
All smoke checks passed
```

After the change:

```
$ cd backend && ../.venv/Scripts/python.exe -m pytest -q
628 passed, 53 warnings in 118.41s (0:01:58)

$ cd web && npx tsc --noEmit
TSC 0 errors

$ npm test
 Test Files  12 passed (12)
      Tests  47 passed (47)

$ npm run api:check
schema.d.ts is up to date

$ npm run build
✓ built in 6.58s

$ SMOKE_PASSWORD='Admin@123' node smoke.mjs http://127.0.0.1:8078
  [PASS] Configuration -> /admin/configuration — 200      (office administrator)
  [PASS] Configuration -> /admin/configuration — 403      (fee collector)
  [PASS] Configuration -> /admin/configuration — 403      (transport manager)
All smoke checks passed
```

626 → 628 backend (the two Settings tests), 45 → 47 web (the two registry
tests). `web/src/api/schema.d.ts` was regenerated with `npm run api:types` after
the route signature changed; the diff is two lines and is in the working tree.

### The new test fails without the fix

`app/api/admin/stats.py` reverted with `git checkout --`, suite re-run, then the
fix restored:

```
$ git checkout -- app/api/admin/stats.py
$ ../.venv/Scripts/python.exe -m pytest tests/test_stats.py -q
        saved = client.patch("/admin/settings", json=body, headers=admin)
>       assert saved.status_code == 200, saved.json()
E       AssertionError: {'detail': [{'type': 'extra_forbidden', 'loc': ['body', 'academic_year'], 'msg': 'Extra inputs are not permitted', 'input': '2025-26'}]}
E       assert 422 == 200
FAILED tests/test_stats.py::test_settings_accepts_its_own_get_body_back
1 failed, 8 passed in 13.72s
--- fix restored ---
```

### The API, directly

One uvicorn on 8078 (`netstat -ano | grep ':8078.*LISTENING'` → a single PID,
checked after every restart), against a freshly dropped, migrated and seeded
`sunrise_test`.

```
GET /admin/configuration (admin)                           200
GET /admin/configuration (counter)                         403
GET /admin/custom-fields?entity=student (admin)            200
GET /admin/custom-fields (counter)                         403
PUT /admin/configuration late_fee.per_day=120 (admin)      200
PUT /admin/configuration (counter)                         403
PUT bad type (string for an int key, admin)                422
PUT unknown key (admin)                                    404
--- value now: 120

--- module off then on
put -> False
auth/me modules: [... 'timetable', 'reports']      (transport gone)
GET /admin/transport/vehicles: 404
after re-enable, vehicles: 200

--- custom field create/retire
POST /admin/custom-fields                                  201  (bus_pass_no)
duplicate key                                              409
key "Bus Pass" (fails the pattern)                         422
select with no options                                     422
counter create                                             403
counter delete                                             403
admin delete                                               204
after retire: [('father_occupation', True), ('house', True), ('bus_pass_no', False)]

--- the Settings 422 fix, live
GET  /admin/settings  → {... "academic_year":"2025-26"}
PATCH the same body back, city changed                     200
```

---

## What I clicked, as whom

**In a real browser**, Chrome against the running Vite dev server on
`http://localhost:5173` talking to the API on `127.0.0.1:8078`. Network status
codes read off the devtools request log, not inferred.

### As `admin@sunrisepublic.edu` (Office Administrator)

| Control | What happened | Status |
|---|---|---|
| Sidebar → **Configuration** | Screen opens, all three cards render | `GET /admin/configuration` 200, `GET /admin/custom-fields?entity=student&include_inactive=true` 200 |
| Modules → **HR and payroll → Turn on** | Pill flips Off → On, **"Staff" appears in the sidebar without a reload** | `PUT` 200, then `GET /auth/me` |
| Modules → **HR and payroll → Turn off** | Confirmation modal, naming what stops ("The staff register, staff attendance, leave and payroll") | modal opened |
| that modal → **Cancel** | closes, nothing sent | — |
| that modal → **Turn it off** | Pill flips On → Off, "Staff" disappears from the sidebar | `PUT` 200 |
| Settings → **Per day = `12.5`** | *A whole number* under the input; **Save changes disabled** (confirmed `button.disabled === true`) | nothing sent |
| Settings → **Per day = `150`** → **Save changes** | button returns to "Saved"; value confirmed as `150` by an independent `GET` | `PUT` 200 |
| Settings → **Save changes** with nothing dirty | button reads "Saved" and is disabled | — |
| Custom fields → **Add a field**, key `bus_pass_no` (already retired) | modal stays open, shows *bus_pass_no is already defined on student* | `POST` 409 |
| that modal → type **select** | the "Options, separated by commas" input appears | — |
| that modal → `travel_mode` / "Travel mode" / select / three options → **Add it** | modal closes, row appears as `select: Own transport, School bus, Walks` | `POST` 201, list refetched 200 |
| Custom fields → **Retire** on Travel mode | modal naming the field and saying values are kept | modal opened |
| that modal → **Retire it** | row flips to "Retired", action cell becomes "—" | `DELETE /admin/custom-fields/4` 204 |
| Custom fields → entity **employee** | empty state: *No custom fields on employee.* | `GET ...entity=employee` 200 |
| Sidebar → **Settings** → academic-year field | **disabled**, `title` = "The current academic year is set on the year record, not here" | — |
| Settings → change City → **Save** | button reads "Saved" — **the first time this control has ever worked** | `PATCH /admin/settings` 200 |

### As `counter@sunrisepublic.edu` (fee collector — should not be able to use it)

| Control | What happened |
|---|---|
| Sidebar after login | Students, Fees, Collect fees, Defaulters, Fee setup, Period close. **No Configuration, no Settings.** |
| Direct navigation to `#/configuration` | *You do not have permission — Configuration needs admin.settings.read, which your role does not hold.* No request was made at all; the route gate refuses before the query. |

Every write on the screen was additionally refused over HTTP with this role's
token: `PUT /admin/configuration` 403, `POST /admin/custom-fields` 403,
`DELETE /admin/custom-fields/{id}` 403.

---

## What I did NOT do

- **Academic year management — dropped, and it is not a scoping decision.**
  There is **no academic-year endpoint anywhere in the backend.** `app/api/`
  contains no route that lists, creates or switches an academic year;
  `services/tenancy.py::set_current_year` exists and **nothing routes to it**
  (`grep -rn "set_current_year" --include=*.py` returns one hit, its own
  definition). A UI here would have had nothing to call. What I did instead was
  stop `/settings` pretending otherwise: its academic-year box is now visibly
  read-only. **To unblock this the backend needs, at minimum, `GET
  /admin/academic-years` and something like `POST
  /admin/academic-years/{id}/make-current` over the existing service.**
- **A role that can read the configuration but not write it was never
  exercised in the browser.** No seeded role holds `admin.settings.read` without
  `admin.settings.write` — the office administrator holds both, and the fee
  collector and transport manager hold neither — so the disabled-with-a-title
  state of the `ActionButton`s on this screen was never seen on screen. The
  refusal itself is verified over HTTP (403 on all three writes as the counter),
  and `ActionButton`'s disabled path has its own test from Packet 0. Worth a
  custom role if the orchestrator wants it seen.
- **Keyboard-first (Enter to submit) is still unproven** on the Add-a-field
  modal, for the reason Part Two of `SESSION-HANDOFF-2.md` records: the browser
  automation's synthetic Return does not trigger form submission, on the
  pre-existing login form either. Every path was verified by clicking. A human
  should press Enter in that modal.
- **`npm run dev` was not started by this session.** Another session's dev
  server was already serving this working tree on 5173 with Vite HMR, and
  `.claude/launch.json` is one of the three pre-existing dirty paths I was told
  not to touch, so I used the running server rather than editing its config to
  claim a different port.
- No commit, no push, no PR. `SESSION-HANDOFF.md`, `.claude/` and
  `reports/README.md` are untouched.

### State the test database was left in

`sunrise_test` was dropped, migrated and re-seeded **after** the final `pytest`
run, so the demo data is clean and current. The values I changed while clicking
(`fees.late_fee.per_day`, the school's city, the HR and Transport switches, two
custom fields) were all in the pre-pytest database and are gone; the seed is as
`seed.py` leaves it.

---

## Defects found in existing code

Reported, not fixed — none is in this packet's files except the first, which was
in scope.

1. **`PATCH /admin/settings` 422 — FIXED, in scope.** Described above.

2. **`DELETE /admin/custom-fields/{id}` writes no audit row and takes no
   reason.** `services/custom_fields.py::retire` flips `is_active` and commits.
   Contract 3 says anything destructive asks for confirmation *and* a reason,
   and `services/audit.py` is where the reason goes — but there is nowhere to
   send one, so the screen confirms without asking for a reason rather than
   collecting one and discarding it. **This is the same defect as the
   `DELETE /admin/notices/{id}` one already on the list** (Part Three item 2 of
   `SESSION-HANDOFF-2.md`), and the two should be decided together: either both
   are audited, or it is written down why a retire is exempt.

3. **`PUT /admin/configuration` is audited but accepts no reason.**
   `services/school_settings.py::set_many` records a before/after audit row with
   `AuditAction.update` and no reason field. Turning a module off makes whole
   departments' screens 404 for every user at the school; the audit records
   *what* changed and never *why*. Less severe than 2 (there is at least a
   record), but the same gap. `SettingsUpdate` would need a `reason` field for
   the UI to send one — `values` is validated against the registry, so a reason
   smuggled in there 404s.

4. **`/admin/configuration` has no `response_model`.** It returns a bare `dict`,
   so `openapi-typescript` types it `{[key: string]: unknown}` and the `Config`
   type in `Configuration.tsx` is a hand-written, unchecked assertion over it —
   the exact shape of the gap that put `₹NaN` on a fee screen. It is documented
   at the top of the file, but a `response_model` on the route would make it
   real. `GET /admin/custom-fields` has the same problem (`list[dict]`), even
   though `_field_out` already produces a fixed shape that a Pydantic model
   would mirror one-for-one.

5. **The `students` module switch can strand the fee counter.** Turning
   `students` off 404s `/admin/students`, which is the search box that is the
   *only* entry point to `/fees/collect` — but `/fees/collect` declares
   `modules: ["fees"]` only, so the screen stays in the sidebar and its search
   silently returns nothing. The row's description on the new screen warns about
   it in words ("the counter can no longer look a child up"), which is a
   mitigation and not a fix. The registry entry for `/fees/collect` arguably
   needs `modules: ["fees", "students"]` — but that is Packet 2's file, and
   `screens.test.tsx` already has a constructed test for the two-module case, so
   it is a one-line change somebody should make deliberately.

6. **Not a defect, but load-bearing and undocumented:** nothing prevents an
   admin from turning off every module including the ones their own screens
   need. `/configuration` is deliberately not module-gated so there is always a
   way back — if a later packet adds a module to that registry entry, a school
   can lock itself out of its own configuration with two clicks.

---

## Files changed

Modified:

```
backend/app/api/admin/stats.py      the PATCH /admin/settings 422 fix
backend/tests/test_stats.py         +2 tests pinning it
web/smoke.mjs                       +1 line: Configuration -> /admin/configuration
web/src/api/schema.d.ts             regenerated (npm run api:types), +2 lines
web/src/auth/AuthContext.tsx        +refresh(), so a module switch updates the sidebar
web/src/pages/Settings.tsx          academic-year input disabled, with a reason
web/src/screens.test.tsx            +2 tests for the new registry entry
web/src/screens.ts                  +the /configuration entry
```

New:

```
web/src/pages/Configuration.tsx     the screen
reports/packet-3-configuration.md   this report
```

Untouched, as instructed: `SESSION-HANDOFF.md`, `.claude/`, `reports/README.md`.
