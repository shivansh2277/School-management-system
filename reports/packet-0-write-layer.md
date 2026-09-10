# Packet 0 — the write layer

Branch `slice/packet-0`, off `main` at `232a791`. Nothing pushed, nothing merged.

## What I built

No screens — the packet forbids them. Five primitives every later packet writes through.

| Deliverable | Where | What it does |
|---|---|---|
| 1. Typed request bodies | `web/src/api/client.ts` | `api.post`/`api.patch` take the body the schema declares, not `unknown`. A misspelt or missing field is now a compile error. |
| 2. Permission-gated controls | `web/src/components/Can.tsx` | `<Can permission>` hides a section; `<ActionButton permission>` disables itself and says which permission is missing. |
| 3. Confirm-with-reason | `web/src/components/ui.tsx` → `ConfirmDialog` | Cannot submit without a non-blank reason; returns the reason the user typed, trimmed. |
| 4. Error surface | `web/src/components/ui.tsx` → `FormField error`, `FormError` | A 422's per-field messages sit next to their inputs; anything else renders instead of vanishing. |
| 5. Write wrapper | `web/src/api/useWrite.ts` | Thin over react-query's `useMutation`: invalidates the keys you name, exposes `fields` for the 422 case. |

**No `useCan` hook.** `AuthContext` already exposes `can` through `useAuth()`; a second
name for the same function is one more thing to keep in step. Reported rather than built.

## The screens.ts entry the orchestrator must add

**None.** Packet 0 adds no screen, so it needs no registry entry. `screens.ts` and
`smoke.mjs` are untouched — deliberately, so packets 1–4 do not conflict on them.

## Verification — commands and their real output

```
$ npx tsc --noEmit
(no output, exit 0)

$ npm test
 Test Files  10 passed (10)
      Tests  41 passed (41)

$ npm run api:check
schema.d.ts is up to date

$ npm run build
✓ built in 4.06s

$ cd backend && ../.venv/Scripts/python.exe -m pytest -q
615 passed, 53 warnings in 129.36s (0:02:09)

$ SMOKE_PASSWORD='Admin@123' node smoke.mjs http://127.0.0.1:8077
All smoke checks passed
```

Baseline was 31 tests in 7 files; now 41 in 10. The ten new tests are in
`client.types.test.ts` (1), `Can.test.tsx` (5) and `ConfirmDialog.test.tsx` (4).

**Backend was not modified.** The 615 above is a clean solo run — see the note in
"What I did NOT do" about an earlier invalid run.

### The typed-body guarantee, proven

`client.types.test.ts` holds six `@ts-expect-error` cases. `tsc` green means every one
is a genuine error; TS reports `TS2578 Unused '@ts-expect-error' directive` otherwise.
I ran a negative control to confirm the mechanism is live, not silently disabled:

```
$ # @ts-expect-error added above a line that correctly compiles
src/api/client.types.test.ts(17,3): error TS2578: Unused '@ts-expect-error' directive.
$ # restored
(no output, exit 0)
```

## What I clicked, as whom

Against the API on :8077 pointed at `sunrise_test`, web on :5173.

| Screen | As | Did | Result |
|---|---|---|---|
| Login | `admin@sunrisepublic.edu` | Signed in | Dashboard, ₹4,72,890.00 in Indian format |
| Notices | admin | Typed a notice, audience `teachers`, clicked Publish | **POST → 201 Created**; row appears with audience `teachers`; form reset |
| Settings | admin | Clicked Save | **PATCH → 422** — a live defect, see below |
| Login | `counter@sunrisepublic.edu` | Signed in | Sidebar shows only Students and Fees; Notices and Settings correctly absent |
| Students | fee counter | Clicked Add Student, filled it, clicked Create student | **POST → 403 Forbidden**, message `This role does not have permission: students.profile.write` |

The notice I published was deleted afterwards (`DELETE → 204`), so the seeded data is
back as it was.

**Screens I did not open:** Dashboard beyond the landing view, Classes, Attendance,
Exams, Fees, Teachers. Packet 0 changes nothing on them.

**The new primitives were not opened in the running app.** They are mounted on no
screen, because this packet adds none. They are proven by component tests that render
and click them in jsdom — `ActionButton` disabled with the right `title` for a role
lacking the permission, `ConfirmDialog` refusing an empty and a whitespace-only reason
and returning the typed one trimmed. That is real evidence, and it is not the same
thing as a clerk using them. The first packet to mount them owes that click-through.

## What I did NOT do

- **No page was wired to `Can`/`ActionButton`.** Contract 3 says "no page checks
  `can()` — that ends with this work". Packet 0 delivers the tools; the pages are not
  in its file list and every one of them belongs to a later packet. **Contract 3 is not
  satisfied yet** — the Add Student 403 above is that gap, live. Whoever takes Packets
  1–4 must wire the nine existing screens, or this stays a library nobody calls.
- **Did not fix the Settings 422** — `Settings.tsx` is Packet 3's territory.
- **`alembic upgrade head` failed** against `sunrise_test` with
  `DuplicateTable: relation "exams" already exists`. Cause: pytest builds the schema
  with `create_all` and leaves no alembic stamp, so a later `upgrade` tries to recreate
  existing tables. `seed.py` succeeded against that schema and the click-through is
  valid, but **`FRONTEND-HANDOFF.md` Part Zero's seed block does not work if the test
  suite has been run first**, which is the normal order it tells you to work in.
- An earlier pytest run reported `70 failed, 491 passed, 54 errors`. It had been started
  while a second suite was running against the same database, and the two clobbered each
  other's schema. Both numbers were invalid; the 615 is a clean solo re-run. Recorded
  because a green number over a contaminated run is the exact failure this project keeps
  hitting.

## Defects found in existing code

1. **`PATCH /admin/settings` always 422s — the Settings Save button has never worked.**
   ```
   {"detail":[{"type":"extra_forbidden","loc":["body","academic_year"],
    "msg":"Extra inputs are not permitted","input":"2025-26"}]}
   ```
   `GET /admin/settings` returns `academic_year`; the page holds the whole response in
   state and PATCHes it straight back; the PATCH model is `extra="forbid"`. Pre-existing:
   `git diff` shows the body my change sends is identical to `main`'s. **My typed bodies
   did not catch this**, because TS's excess-property check applies only to object
   literals and `form` is a variable — an honest limit of deliverable 1.

2. **`DELETE /admin/notices/{id}` writes no audit row.** `services/notices.py::delete`
   deletes and commits without calling `services/audit.py::record`. Every other
   destructive path is audited with a reason; this one is not, so it also never triggers
   the reason requirement. Either it should be audited, or the asymmetry should be
   written down.

3. **Dates render US-style.** The Notices list showed `9/10/2026` for 10 September —
   `toLocaleDateString()` with no locale follows the browser. Part Three rule 6 requires
   `dd/mm/yyyy`. Affects every screen using the bare call.

4. **`npm run api:check` could never pass on Windows.** Fixed in this branch's first
   commit, `563e7d8`, before any packet work. `core.autocrlf=true` with no
   `.gitattributes` checked the generated file out as CRLF while the generator writes LF,
   so all 14,720 lines "differed" — a byte delta of exactly 14,720. The drift guard was
   dead for any Windows developer and passed in CI only because CI is Linux.

5. **The generator marked defaulted fields as required in request bodies.**
   `openapi-typescript`'s `defaultNonNullable` made `password: string` mandatory on
   `GuardianInput`, which would have forced every caller to hardcode the backend's own
   `"Parent@123"` — duplicating a policy constant into the client, and pre-empting the
   account-issuing decision `CLAUDE.md` records as deliberately unmade. Turned off in
   `scripts/generate-api-types.mjs`. Cost measured, not assumed: 152 response properties
   become optional, and zero new `tsc` errors across all nine screens.

## Files changed

Commit `563e7d8` — the prerequisite:

```
A  .gitattributes
```

Packet 0 proper:

```
M  web/scripts/generate-api-types.mjs   defaultNonNullable:false, with the reasoning
M  web/src/api/client.ts                Body<>, BodyArg<>, typed post/patch
M  web/src/api/schema.d.ts              regenerated (never hand-edited)
M  web/src/components/ui.tsx            ConfirmDialog, FormError, FormField error prop
A  web/src/api/client.types.test.ts     six @ts-expect-error cases
A  web/src/api/useWrite.ts              the write wrapper
A  web/src/components/Can.tsx           Can, ActionButton
A  web/src/components/Can.test.tsx      5 tests
A  web/src/components/ConfirmDialog.test.tsx  4 tests
A  reports/packet-0-write-layer.md      this report
```

Two call sites the typed bodies forced, both genuine, both outside the packet's file
list and both minimal:

```
M  web/src/pages/Notices.tsx    audience state was `string`; now the API's union
M  web/src/pages/Settings.tsx   Save posted `null` before the school query resolved
```
