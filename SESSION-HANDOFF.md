# Session handoff — 9 September 2026

**For the next session, starting cold.** This covers one long session that ran
8–9 September and produced **41 commits** (`040c189..a26c7cf`). The branch now
carries **110 commits and has never been pushed.**

`HANDOFF.md` remains the canonical project document — architecture, every
commit and why, the traps, the open questions. This file is narrower: what
happened in *this* session, what is verified, and what to pick up next. Read
`CLAUDE.md`, then `HANDOFF.md` §2 and §4, then this.

---

## 1. Verified state — measured, not recalled

Re-run these before trusting anything below. Numbers stale on the next commit.

```bash
cd backend
../.venv/Scripts/python.exe -m pytest -q                 # 603 passed, ~2 min
cd ../web
npx tsc --noEmit                                         # 0 errors
npm test                                                 # 24 tests, 7 files
npm run api:check                                        # schema up to date
npm run build                                            # succeeds
```

| Measure | Value |
|---|---|
| Backend tests | **603 passing** (was 522 at session start) |
| Web tests | **24** in 7 files (was **0**) |
| `tsc --noEmit` | **0 errors** |
| API surface | 214 paths, 263 operations |
| Report library | 21 reports, 9 categories |
| Branch | `part-1-foundation`, **110 commits, never pushed, CI never run** |

The by-hand Postgres check in `HANDOFF.md` §4 (drop schema → migrate → seed →
worker) was last run clean on 8 September. **Re-run it after any migration.**

---

## 2. What this session did, in order

**Part 4 reports (the last backend module).** 21 reports in a code registry
(`app/core/report_registry.py`), a gate (`app/services/reports.py`), a library,
viewer and audited CSV export. No new tables — the reasoning for rejecting
§5.10.5's eight entities is in the registry docstring. Every backend module of
Parts 1–4 is now built.

**A live sweep of the whole API** as all six demo roles against a real uvicorn
server on a seeded database. `functions.md` is its record. **578 tests were
passing throughout and it found eight defects anyway** — three endpoints nothing
ever called (returning 500 to their own role), a number nothing ever questioned
(`/teacher/classes` reported every class as 1000 students, a cartesian product),
and two permission gates that passed the role check and skipped the row check.

**Web ERP workstream, Slice 0.** The API was 214 paths behind a 9-page UI. The
workstream was decomposed into a foundation slice plus six module slices, and
Slice 0 was designed, planned and built through seven reviewed tasks. Spec and
plan are in `docs/superpowers/{specs,plans}/2026-09-08-web-erp-slice-0-*`.

---

## 3. Pick up here

### 3.1 Before Slice 1 — three things, cheapest now

From the final review. Each gets monotonically more expensive per slice added.

1. **The screen registry takes one permission and one module per screen, but a
   screen makes several calls.** `web/src/screens.ts` — make it `permissions[]`
   and `modules[]`. `/settings` already crosses the `fees` module gate without
   declaring it. Nine entries to change now; sixty later.
2. **`web/smoke.mjs` does not do what the spec said.** It only checks for 404s.
   It should import `screens.ts`, derive the nav from the live `/auth/me`, and
   assert visible screens answer 200 while hidden ones answer 403/404. Twenty
   lines, and it would then catch this whole class of bug forever, for every
   screen the next six slices add.
3. **Request bodies are untyped.** `api.post/patch` take `body?: unknown` while
   the generated schema types `requestBody` right there. Slices 1–6 are mostly
   writes — the half they depend on is the unchecked half.

### 3.2 Backend, scheduled

4. **Four routers declare module gates the backend does not enforce** —
   `students.py`, `exams.py`, `notices.py`, `teachers.py` have no
   `module_enabled`. A school switching `examinations` off hides the screen from
   the office while the API keeps serving the mobile app. Do this before any
   school is offered a module switch.
5. **Admin fee routes have no response models**, so FastAPI serialises `Decimal`
   as a JSON **float** — `/admin/fees/invoices`, `/plans`, `/collection`,
   `/ledger/{id}`, `/daybook`, `/defaulters`. Nothing is corrupted today (all
   read-only display, values small), but **Slice 2 posts money back through this
   layer.** Fix before Slice 2, not during.

### 3.3 The other candidates

- **`CONFIGURATION-GUIDE.md`** — the last item of Checkpoint 4, now unblocked;
  every module it must describe exists. `EXTENSION-GUIDE.md` after it. **The
  owner asked for both to be held until told; check before writing.**
- **Slice 2a — printing.** There is **no admin-side receipt PDF anywhere in the
  API**; the only PDF route is under `/parent`. A counter clerk who takes cash
  cannot print a receipt, so the Money slice is not shippable without it.
- **Four of six communication senders still unwired** (`HANDOFF.md` §9).
- **Push and CI.** 110 commits, never pushed. The first push is the first CI
  run, and CI now also runs the web job's typecheck, tests and schema check.

---

## 4. Traps this session added — read before touching these areas

**Clock-dependent tests are endemic here, and four were fixed.** The suite was
green at 16:26, red at 22:37, green after a fix, red again at 23:15 — on
identical code. Two comms tests failed for ten hours a day (quiet hours are
21:00–07:00 and `send()` schedules instead of dispatching inside them); a quiet
hours test set its window to `0..23` and claimed in its docstring that covered
the whole day, but `inside` is `start <= hour < end` so hour 23 fell outside; and
an admission test scheduled work "an hour from now" and asserted it fell in
today. **CI runs in UTC, five and a half hours from the office, so it meets every
one of these boundaries at a different moment than you do.** A fifth remains
unfixed and is recorded rather than chased: `test_a_read_never_moves_a_stored_status`
fails if the date rolls over mid-run. It passed on re-run.

**A cartesian product is silent in SQLAlchemy and loud only in the server log.**
`db.query(Student).filter(Enrolment.x == y).count()` names two tables and joins
neither, counting the cross product — 1000 for a class of ten. It emits
`SAWarning`, which no test reads. **Grep the server log for SAWarning after any
sweep.**

**A test that mirrors the implementation agrees with a bug forever.**
`test_totals_match_direct_counts` recomputed "every active employee" and asserted
the code matched, so it passed while the Transport Manager was counted as a
teacher. Assert the intent, not the query.

**A whole-school read must narrow a teacher itself.** A teacher holds most
`.read` permissions school-wide with the restriction in the service, so
`require_permission(school_wide=True)` stops a guardian and nobody else. Any
route or report answering across sections calls
`scoping.narrow_to_own_sections()`. Two attendance screens and the student roster
skipped it.

**The web app's types are generated. Never hand-edit `web/src/api/schema.d.ts`.**
Regenerate with `npm run api:types`; `npm run api:check` fails if it is stale.

---

## 5. Decisions the owner made this session

- A teacher sees **only their own class**, for attendance and for the student
  roster. Both were school-wide; both are narrowed.
- The attendance shortage threshold is now a **setting**
  (`attendance.shortage_threshold`, default 75), not a constant.
- The web ERP target is **"a real school could run on it"** — full CRUD, not a
  demo. That is what forced the decomposition into seven slices.
- The web app is **staff-only**; teachers, students and guardians stay on the
  mobile app.
- The student roster narrowing was chosen over blocking teachers entirely.

---

## 6. What is NOT verified

Stated so nothing here is mistaken for a broader claim.

- **Nothing is deployed.** No hosting, no backup, no restore drill, no
  monitoring. CI has never executed.
- **No load or concurrency testing.** "No query is slow" is an assumption at 100
  students — it is the stated reason the four report summary tables were not
  built.
- **The mobile app itself is untested**; its API endpoints are now exercised.
- **No browser testing of the web app.** Endpoints and rendered sidebars are
  tested; screens have not been opened by an automated browser. Three demo
  logins were walked through by hand.
- **No real email has been sent**; the provider sits behind a seam.
- **PDFs generate but nobody has read one as a document.**

---

## 7. Session artefacts worth keeping

- `functions.md` — every function and feature with the measured result of
  running it, plus the eight defects the sweep found.
- `docs/superpowers/specs/2026-09-08-web-erp-slice-0-foundation-design.md` — the
  workstream decomposition and the six decisions behind it.
- `docs/superpowers/plans/2026-09-08-web-erp-slice-0-foundation.md` — the
  executed plan.
- `.superpowers/sdd/2026-09-08-web-erp-slice-0-foundation/` — **gitignored**, but
  kept deliberately: the execution ledger with every ruling made, the per-task
  reports, and the final review's nine findings in full. Delete only when the
  scheduled findings in §3 are done.
