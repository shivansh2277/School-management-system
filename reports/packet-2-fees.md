# Packet 2 — Fees at the counter

Branch `slice/office-feedback`, off `slice/packet-0`, off `main` at `232a791`.
Nothing pushed, nothing merged. The branch also carries the office's own change
requests, which arrived mid-packet; they are listed at the end.

## What I built

| Route | What a clerk does on it | Endpoints |
|---|---|---|
| `/fees/collect` | Find a child, see the account, take the money, read back a receipt number. Reverse a receipt. | `GET /admin/students`, `GET /admin/fees/ledger/{student_id}`, `POST /admin/fees/payments`, `POST /admin/fees/payments/{id}/reverse` |
| `/fees/defaulters` | Who owes what, worst first, with a number to ring. | `GET /admin/fees/defaulters`, `GET /admin/classes` (filter, gated at the widget) |
| `/fees/setup` | The plans a class is charged, and the concessions granted against them — including the approval step. | `GET/POST /admin/fees/plans`, `GET /admin/fees/heads`, `GET/POST /admin/fees/concessions`, `POST /admin/fees/concessions/{id}/decide`, `POST /admin/fees/concessions/sibling-sweep`, `GET /admin/fees/invoices` (to name an enrolment) |
| `/fees/periods` | Close a month's books, or reopen one. | `GET /admin/fees/periods`, `POST /admin/fees/periods/{year}/{month}/close`, `.../reopen` |

Fee **heads** went onto `/settings` instead of here — they are school
configuration, not a per-year decision, and the office asked for fee structure
to be editable from Settings.

## The screens.ts entries

All four are already committed to `screens.ts` on this branch, because I am
running the packets sequentially rather than as parallel subagents, so there is
no orchestrator to hand them to. Reproduced here so they can be reviewed as a
set. Every permission was read off the backend router named beside it.

```ts
{ path: "/fees/collect",    label: "Collect fees", group: "Money",
  permissions: ["fees.invoice.read", "students.profile.read"], modules: ["fees"] }
// fees.py (admin_only) + students.py (admin_only). Both required to load: the
// student search IS the entry point, not a secondary widget.

{ path: "/fees/defaulters", label: "Defaulters",   group: "Money",
  permissions: ["fees.invoice.read"], modules: ["fees"] }
// fees.py. /admin/classes is undeclared and gated at the widget - a fee
// collector holds fees.invoice.read without academics.class.read.

{ path: "/fees/setup",      label: "Fee setup",    group: "Money",
  permissions: ["fees.invoice.read"], modules: ["fees"] }
// fee_setup.py reader + fees.py. Writes (fees.setup.manage,
// fees.concession.approve) gate themselves on their buttons.

{ path: "/fees/periods",    label: "Period close", group: "Money",
  permissions: ["fees.invoice.read"], modules: ["fees"] }
// fees.py. Close/reopen need fees.payment.void, which gates the button rather
// than hiding the screen from a clerk who needs to see whether a month is shut.
```

`web/smoke.mjs` was updated for all four. Its `Collect fees` entry resolves a
real student id rather than hardcoding one, because that route 404s for an
unknown student as well as for a deleted endpoint and conflating those is the
exact failure the script exists to catch — the seeded roster starts at 125.

## Verification — commands and their real output

```
$ cd web && npx tsc --noEmit
(no output, exit 0)

$ npm test
 Test Files  11 passed (11)
      Tests  43 passed (43)

$ npm run api:check
schema.d.ts is up to date

$ npm run build
✓ built in 7.84s

$ cd backend && ../.venv/Scripts/python.exe -m pytest -q
623 passed, 53 warnings in 168.44s (0:02:48)

$ cd web && SMOKE_PASSWORD='Admin@123' node smoke.mjs http://127.0.0.1:8078
All smoke checks passed
```

Baseline at the start of this work was 31 web tests in 7 files and 615 backend
tests. Backend is 623 because of the eight in `tests/test_class_listing.py`,
added for the office's ordering and curriculum reports.

**No backend file changed in the final commit of this packet**, so the 623
above stands for it; `git status backend/` was empty before I claimed it.

## What I clicked, as whom

API on :8078 against `sunrise_test`, web on :5173.

| Screen | As | Did | Result |
|---|---|---|---|
| `/fees/collect` | fee counter | Searched `2024000001`, opened the account, took ₹7,200 | **One POST → 201**, receipt `SPS/RCP/2026/000171`, outstanding ₹7,200 → ₹0.00, all three invoices allocated oldest-first to `paid` |
| `/fees/collect` | fee counter | Hovered the Reverse buttons | Disabled, `title="Your role does not hold fees.payment.void"` |
| `/fees/collect` | admin | Reversed that receipt with a typed reason | Contra receipt at **−₹7,200.00**, original kept and marked `reversed`, both then offer no Reverse button |
| `/fees/defaulters` | admin | Loaded, then filtered `min_amount=9000` | 100 students worst-first → exactly the 6 owing more than ₹9,000 |
| `/fees/defaulters` | fee counter | Loaded | Chase list intact; class filter absent (no `academics.class.read`) |
| `/fees/periods` | admin | Closed June 2026 with a reason | **POST → 200**, status `closed`, reason on record, button became Reopen |
| `/fees/periods` | admin | Tried to bill into the closed month | `generate 2026-06` → **409** `"2026-06 is closed"`; open May → **200** |
| `/fees/periods` | admin | Reopened June with a reason | Back to `open` |
| `/fees/periods` | fee counter | Loaded | All 12 Close buttons disabled, `fees.payment.void` named |
| `/fees/setup` | admin | Loaded | 10 plans in class order 1→10 with heads and amounts; 2 concessions with **names resolved**, not enrolment ids |
| `/fees/setup` | admin | Approved a `requested` concession with a reason | **POST decide → 200**, status `approved`, buttons correctly vanished |
| `/fees/setup` | fee counter | Loaded | Add plan and Run sibling sweep both disabled, `fees.setup.manage` named |

**Not opened:** the Add plan form was built and type-checks but I did not
create a plan through it against the live API — the seeded school already has a
plan for every class, and adding an eleventh would have left demo data I would
then have had to unpick. **It is unverified, and it is the one control on this
packet that is.**

Everything I did change in the demo database was undone: the test payment was
reversed, June was reopened, and the database was finally dropped, migrated and
re-seeded from scratch, after which smoke passed again.

## What I did NOT do

- **Plan assignment** (`POST /admin/fees/assignments`, plan → enrolment) is not
  built. It needs an enrolment picker, and see the blocked dependency below.
- **Requesting a concession** from the UI is not built; only deciding one is.
  Same reason — a request names an `enrolment_id` the UI cannot obtain cleanly.
- **No receipt PDF.** The packet flagged this and it is still true: the only
  PDF route is `/parent/fees/receipts/{payment_id}.pdf`. A counter clerk cannot
  print. The collect screen shows the receipt number and offers no print
  button, rather than opening the parent route.
- **Keyboard-first is unverified, not built or broken.** Enter did not submit
  any form through the browser automation — including the pre-existing login
  form, which is how I know it is the harness and not the app. The click paths
  are all verified. A human should confirm Enter works on the search box and
  the amount field.

## Defects found in existing code

1. **`ActionButton` could fire every write twice.** A `<button>` with no `type`
   defaults to `submit`, so one click on Take ran `onClick` *and* the form's
   `onSubmit`. Only the idempotency key stood between that and taking a payment
   twice — a guard, not a licence. Fixed in the shared component with a test
   that fails without it.
2. **The query cache outlived the session — a permission bypass.** After
   signing out of admin and in as the fee counter, the admin's cached class
   list was still there, and for a query the new role may not make at all the
   request never returns, so the stale answer stands. The counter PC in a
   school office is shared. `logout()` now clears the cache; pinned by a test.
3. **`PATCH /admin/settings` always 422s** — `academic_year` is returned by the
   GET and forbidden by the PATCH. Pre-existing on `main`. Still unfixed:
   Settings is Packet 3's territory.
4. **`DELETE /admin/notices/{id}` writes no audit row**, unlike every other
   destructive path. Unfixed, reported.
5. **Five listings ordered classes lexicographically** — 1, 10, 2. Fixed
   against the office's report; see below.
6. **`money()` renders `₹NaN`** for an absent value rather than failing. It hid
   my own wrong field name on a live fee screen with `tsc` green. Not changed —
   the root cause was the type, but a money helper that can print NaN on a fee
   screen is worth a decision.

## Blocked dependency, reported rather than faked

**No endpoint maps a student to their `enrolment_id`.** `/admin/students` and
`/admin/students/{id}` both omit it; only rows that already carry money
(`invoices`, `defaulters`, `ledger.invoices`) do. Consequences, all live:

- A student with **no invoices cannot be paid for at all** — the collect screen
  says so plainly instead of showing a dead form.
- Concession rows are named by joining through `/admin/fees/invoices`, which
  works only because every seeded student has one.
- Plan assignment and concession *requests* are not built.

The clean fix is `enrolment_id` on the student row, or a small
`/admin/enrolments?student_id=` lookup. That is a backend change and outside
this packet.

## The office's change requests (same branch)

Raised after the counter screens landed, applied as `f6da429` and `6f51578`:

- **Class 10 sorted after class 1.** One root cause, five listings — classes,
  the Settings fee structure, the admission cycle's classes, seat usage and the
  public portal. One shared key in `services/common.py` now.
- **Every class taught the same six subjects.** Primary (1–5) now takes
  Environmental Studies, Computer and Art & Craft; classes 6–10 take Science,
  Social Science and Sanskrit. Six per stage is load-bearing: ten sections must
  be taught in all thirty periods, so ten of twelve teachers are busy every
  period and only one-specialist-per-stage-per-subject keeps the grid solvable.
  A seventh subject is left out rather than faked.
- **Students:** a Fees column (paid / amount owed), editing a student, and
  emailing defaulters.
- **Dashboard:** Today's Schedule replaced by Upcoming Events. PTMs and
  meetings exist in no table anywhere, so none are shown and the card says so.
- **Settings:** grading system and fee structure are editable.

## Files changed

Packet 2 proper:

```
A  web/src/pages/CollectFees.tsx
A  web/src/pages/Defaulters.tsx
A  web/src/pages/FeeSetup.tsx
A  web/src/pages/FeePeriods.tsx
M  web/src/screens.ts                 four entries
M  web/smoke.mjs                      four entries, one resolving a real id
M  web/src/components/Can.tsx         type="button"
M  web/src/components/Can.test.tsx    the test that pins it
M  web/src/auth/AuthContext.tsx       clear the query cache on logout
A  web/src/auth/AuthContext.test.tsx  the test that pins it
A  reports/packet-2-fees.md           this report
```

Commits: `08ad0b7` (collect), `e8d2aef` (defaulters + cache fix), `2a24c0f`
(setup, concessions, period close). The office's requests are `f6da429` and
`6f51578`; Packet 0 is `563e7d8` and `61a01f6`.
