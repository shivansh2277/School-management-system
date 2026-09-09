# Session handoff — next session's brief

**Written 9 September 2026.** The previous session ran 8–9 September and
produced 41 commits (`040c189..a4a0bdf`). The branch carries **112 commits**;
the repo exists on GitHub but **this branch has never been pushed**.

`HANDOFF.md` stays canonical for architecture, the commit history and the
traps. `CLAUDE.md` has the house rules. **This file is your brief: three fixes,
then a test pass, then the first push.** Do them in that order.

---

# PART ONE — the three fixes, in order

## Fix 1 — the screen registry allows one permission and one module per screen

**Where:** `web/src/screens.ts`

Every screen declares a single `permission` and an optional single `module`. But
a screen makes several API calls, and they do not all sit behind the same gate.
This is the same defect class that was already found and fixed once in this
workstream — the attendance screen was gated on an exam permission — and the
registry's shape means it will keep recurring.

**The live instance:** `/settings` declares `permission: "admin.settings.read"`
and **no module at all**, but `Settings.tsx` calls `/admin/fees/plans`, which
sits behind `module_enabled("fees")` in `app/api/admin/fee_setup.py`. A school
with the fees module off opens Settings and the fee-structure panel fails.

**A latent instance:** `/exams` declares `exam.definition.read`, but the page
also calls `/admin/subjects`, which needs `academics.class.read`. No system role
breaks today — every role holding the first holds the second — but a school
defining a custom role breaks it immediately.

**What to do:** change `Screen` to take `permissions: string[]` and
`modules?: ModuleCode[]`. Update `visibleScreens` and `RequirePermission` to
require **all** of them. Update the nine entries. Then walk each page, list the
endpoints it actually calls, and declare the real set — do not guess from the
screen's name.

**Why now:** nine entries to change today, sixty after six more slices. This is
the single cheapest-now/expensive-later item on the list.

**Test it with:** extend `web/src/screens.test.tsx` — a screen declaring two
permissions must be hidden from a caller holding only one, and a screen
declaring two modules must be hidden when either is off.

---

## Fix 2 — eleven backend routers declare module gates that are not enforced

**This is the security-shaped one. Do not defer it.**

`core/modules.py` gives each school a `feature.<module>` switch, and
`school_settings.module_enabled()` is the dependency that enforces it at the
route. Fourteen routers use it. **Eleven do not**, and several of those serve
modules the switch claims to control.

**The sharpest case — HR defaults to OFF for every new school:**

```
core/modules.py:  Module("hr", "HR and payroll", built=True, default_enabled=False)
```

and **none** of its five routers is gated:

| Router | Serves | Module gate |
|---|---|---|
| `app/api/admin/hr.py` | staff records, departments | **NO** |
| `app/api/admin/payroll.py` | salary structures, runs, payslips | **NO** |
| `app/api/admin/staff_attendance.py` | the staff register | **NO** |
| `app/api/admin/staff_leave.py` | leave and balances | **NO** |
| `app/api/admin/teachers.py` | the staff list | **NO** |

So a brand-new school that has never switched HR on has its **entire staff and
payroll surface live** — salary structures, payslips, payroll runs. Permissions
still apply, so it is not open to everyone; but the feature flag the product
sells as "this module is off for you" does nothing at all.

**The others:**

| Module | Ungated routers |
|---|---|
| `examinations` | `exams.py`, `grading.py`, `schemes.py`, `report_cards.py` |
| `students` | `students.py` |
| `communication` | `notices.py` (`comms.py` is already gated) |

`classes.py`, `settings.py` and `stats.py` have no module in the registry and
are correctly ungated — leave them.

**What to do:** add
`dependencies=[Depends(module_enabled("<code>"))]` to each router above, the way
`attendance.py`, `transport.py` and `comms.py` already do it. Then add a test per
module asserting that switching the flag off makes its endpoints 404 — the
pattern exists in `tests/test_reports.py::test_a_module_that_is_off_has_no_reports`.

**Watch for:** `hr` and `transport` default to **off**, so the moment you gate
these routers, any existing test that touches HR or payroll without enabling the
module will start failing. That is the gate working. Enable the module in those
tests (there is an `all_modules` fixture in `tests/test_reports.py` to copy),
do not weaken the gate. Expect the suite to go red before it goes green.

**The rule this restores** is already written in `school_settings.module_enabled`'s
own docstring: *"A switch the UI honours and the API does not is not a switch."*

---

## Fix 3 — stabilise the date-dependent test properly

**Where:** `backend/tests/test_fees.py::test_a_read_never_moves_a_stored_status`

Four clock-dependent tests were fixed last session. This is the fifth and it was
recorded rather than chased, because it is rarer and of a different kind: it does
not fail during a particular hour, it fails when **the date rolls over in the
middle of a suite run**. It was seen once, when a run started on 8 September and
finished on 9 September. It passes alone and on re-run.

**What to do:** find what it compares against `Date.today()` and pin the date
instead of reading it twice. Do not paper over it with a retry. The other four
fixes are the model: make the test state the date it means rather than asking
the clock twice and hoping the answers match.

**While you are there,** it is worth grepping the suite for the same shape —
`Date.today()` or `datetime.now` called more than once in a single test, or a
value built from `now` and asserted against a window computed from the local
day. That pattern has now produced five defects in this codebase.

---

# PART TWO — then test it

Run all of it, and read the output rather than the exit code.

```bash
# Backend — expect 603 passing plus whatever Fix 2 and Fix 3 add
cd backend
../.venv/Scripts/python.exe -m pytest -q

# The by-hand Postgres check — migrations from empty, seed, worker
export DATABASE_URL=postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test
../.venv/Scripts/python.exe -c "
from sqlalchemy import create_engine, text
import os
with create_engine(os.environ['DATABASE_URL']).begin() as c:
    c.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public'))"
../.venv/Scripts/python.exe -m alembic upgrade head
BCRYPT_ROUNDS=4 ../.venv/Scripts/python.exe seed.py
../.venv/Scripts/python.exe worker.py --once

# Web — all four must pass
cd ../web
npx tsc --noEmit          # 0 errors
npm test                  # 24 tests before your changes; more after Fix 1
npm run api:check         # schema current — Fix 2 changes the schema, so regenerate
npm run build

# Live — start the backend on 8077 first, in another terminal.
# NOTE the env var: without it uvicorn talks to the stale dev database, which is
# several parts behind and looks exactly like a bug in whatever you are probing.
cd ../backend
DATABASE_URL=postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test ../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8077

# then, back in web/
node smoke.mjs http://127.0.0.1:8077
```

**Fix 2 changes the OpenAPI schema** (gated routes gain a 404 response). Run
`npm run api:types` and commit the regenerated `web/src/api/schema.d.ts`, or
`api:check` will fail in CI.

**Then test the module switch by hand**, because that is the thing being fixed:
turn `feature.hr` off via `PUT /admin/configuration`, confirm `/admin/payroll/runs`
404s, turn it on, confirm it answers. A test proves it in CI; doing it once by
hand proves the test is testing the right thing.

---

# PART THREE — then push to GitHub

**Read this carefully — the framing matters.** The *repository* already exists
on GitHub and `origin/main` is there; it holds the v0 school management system.
What has never been pushed is **this branch**, `part-1-foundation`, which is
**112 commits ahead of `main`** and contains the entire ERP. So this is not the
project's first push, but it is the first time any of this work leaves the
laptop, and **CI has genuinely never executed** — `.github/workflows/ci.yml`
triggers on `push: branches: [main, "part-*"]`, so pushing this branch will fire
it for the first time.

**Before pushing, show the owner the exact file list and wait for an explicit
go-ahead.** That is a standing rule in `CLAUDE.md` and in the owner's stated
preferences. It is not optional and a summary does not satisfy it.

```bash
git status --short                        # must be empty
git log --oneline main..HEAD | wc -l      # 112 at handoff, plus your fixes
git diff --stat main..HEAD                # the exact file list to show
git remote -v                             # origin = shivansh2277/School-management-system
```

**There is a decision here that is the owner's, not yours.** Ask which:
- push `part-1-foundation` as a branch (CI runs, `main` untouched, nothing is
  merged) — the lowest-risk option and the natural first move;
- open a pull request from it into `main`;
- merge into `main` locally and push that.
Do not pick one on the owner's behalf. Pushing a branch is reversible; merging
112 commits into `main` is the kind of step that should be asked about.

**Expect the first CI run to fail, and say so before it does.** It has never
executed, it now has a backend job and a web job, and it runs in UTC — five and
a half hours from the office, which is exactly where four clock-dependent tests
were already found. A red first run is information, not a sign that something
broke locally. Budget a round of CI fixes after the push.

**Check before pushing:** `backend/var/` is gitignored (it once staged 302
uploaded PDFs), no `.env` or credential is staged, and `web/smoke.mjs` contains
three demo passwords — seed credentials, low stakes, but the owner should know
they are going public.

---

# PART FOUR — context you will need

## Verified state at handoff

Re-measure before trusting; these go stale on the next commit.

| Measure | Value |
|---|---|
| Backend tests | **603 passing**, ~2 min |
| Web tests | **24** in 7 files (there were none before this workstream) |
| `tsc --noEmit` | **0 errors** |
| API surface | 214 paths, 263 operations |
| Branch | `part-1-foundation`, **112 commits ahead of `main`, branch never pushed, CI never run** |

## Traps — read before touching these areas

**Clock-dependent tests are endemic.** The suite was green at 16:26, red at
22:37, green after a fix, red again at 23:15 — on identical code. Comms quiet
hours are 21:00–07:00 and `send()` schedules instead of dispatching inside them.
CI runs in UTC, so it meets every one of these boundaries at a different moment
than you do. Fix 3 is the fifth instance.

**A cartesian product is silent in SQLAlchemy and loud only in the server log.**
`db.query(A).filter(B.x == y).count()` names two tables and joins neither. It
emits `SAWarning`, which no test reads. Grep the server log after any sweep.

**A test that mirrors the implementation agrees with a bug forever.** One
recomputed "every active employee" and asserted the code matched, so it passed
while a bus manager was counted as a teacher. Assert the intent.

**A whole-school read must narrow a teacher itself.** Teachers hold most `.read`
permissions school-wide with the restriction in the service, so
`require_permission(school_wide=True)` stops a guardian and nobody else. Call
`scoping.narrow_to_own_sections()`.

**`web/src/api/schema.d.ts` is generated.** Never hand-edit it.

**The demo school's id is not 1.** Read it from `schools`.

## Decisions the owner has made

- A teacher sees **only their own class** — attendance and student roster both.
- The attendance shortage threshold is a **setting**, not a constant.
- The web ERP target is **"a real school could run on it"** — full CRUD.
- The web app is **staff-only**; teachers, students and guardians use mobile.
- `CONFIGURATION-GUIDE.md` and `EXTENSION-GUIDE.md` are **held until the owner
  says otherwise.** Do not write them unprompted.

## What is NOT verified

- **Nothing is deployed.** No hosting, backup, restore drill or monitoring.
- **No load or concurrency testing.** "No query is slow" is an assumption at 100
  students.
- **The mobile app is untested**; its API endpoints are exercised.
- **No browser automation** of the web app; three demo logins were walked by hand.
- **No real email sent.** PDFs generate but none has been read as a document.

## After these three fixes

In `docs/superpowers/specs/2026-09-08-web-erp-slice-0-foundation-design.md` §8:
Slice 1 (Students + Admission), **Slice 2a (printing — there is still no
admin-side receipt PDF, so a counter clerk cannot print a receipt)**, then Money,
Academics, Staff, Operations, Insight. Two smaller items also remain: the
`smoke.mjs` script should derive the nav from `screens.ts` rather than only
checking for 404s, and `api.post/patch` still take `body?: unknown` while the
generated schema types `requestBody` — Slices 1–6 are mostly writes.

## Artefacts

- `functions.md` — every function with the measured result of running it.
- `docs/superpowers/{specs,plans}/2026-09-08-web-erp-slice-0-*` — the design and
  the executed plan.
- `.superpowers/sdd/2026-09-08-web-erp-slice-0-foundation/` — **gitignored**, kept
  deliberately: the ledger of every ruling, the per-task reports, and the final
  review's nine findings in full. Delete once Fixes 1–3 are done.
