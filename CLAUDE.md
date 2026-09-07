# CLAUDE.md — Sunrise School ERP

## Read these first, in this order

1. **`HANDOFF.md`** (this directory) — current state, the commits and why each
   exists, and what is explicitly *not* verified.
2. **`docs/ERP_BLUEPRINT.md` §0** — the 21 locked product decisions. **§0 wins
   over anything else in that document**; the rest was written before those
   answers and is corrected only where it would mislead.
3. **`docs/ERP_BLUEPRINT.md` §12** — the four-part delivery plan.

`docs/BLUEPRINT.md` is the original v0 build contract. Still useful for the
reasoning behind the original design, but superseded wherever the ERP blueprint
disagrees.

## What this is

A multi-tenant school ERP being sold to **separate, independent schools** — not
branches of one school. A tenant is a customer. Work is on branch
`part-1-foundation`; **nothing has been pushed**.

## Commands

```bash
cd backend
../.venv/Scripts/python.exe -m pytest -q          # 292 tests, ~78s
../.venv/Scripts/python.exe -m pytest tests/test_rbac.py -q       # one file
../.venv/Scripts/python.exe -m alembic upgrade head
../.venv/Scripts/python.exe seed.py               # idempotent
../.venv/Scripts/python.exe worker.py --once      # drain the job queue
../.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000

cd web && npx tsc --noEmit && npm run dev
```

Postgres runs natively on this machine, not in Docker. `make testdb` uses
`docker compose exec` and fails here — create `sunrise_test` by hand.

## Architecture rules that matter

- **Three layers.** `api/` is thin, `services/` holds the rules, `models/` holds
  the schema. Business logic does not live in a route.
- **Permission at the route, scope in the service.** `require_permission()`
  decides *may you at all*; `services/scoping.py` decides *over which rows*.
  Keep them separate.
- **Every table carries `school_id`.** It is declared on `TenantBase` so a new
  table cannot quietly be created without one. A missing tenant key is a data
  leak between customers, not a style problem.
- **Year-scoped facts join through `enrolment_id`; lifetime facts through
  `student_id`.** Getting this backwards reintroduces the bug the enrolment
  split exists to fix.
- **Reads never write.** Nothing in a GET may commit.
- **Business rules belong in database constraints** where they can be — unique
  constraints, partial indexes, foreign keys — not only in Python.
- **Staff are `employees`, not `teachers`; `guardians`, not `parents`.** The
  columns that name a teaching role in context — `class_teacher_id`,
  `class_subject_teacher.teacher_id` — keep their names on purpose, as do the
  `/teacher` and `/parent` URL prefixes the mobile app calls.
- **An applicant is not a user.** Nothing in Admission may require a
  `students` or `users` row: most applicants never get one. The links that do
  exist — a sibling, a staff parent — are claims until verified, and an
  unverified claim must never influence a decision.
- **Per-school configuration goes through the registries**, not through new
  columns: `core/settings_registry.py` for settings and feature flags,
  `custom_fields` for school-invented attributes. A feature flag is a boolean
  setting named `feature.<module>`, and it is enforced at the route.
- **Money is `Numeric`, never float. Timestamps are `timestamptz`.** Round with
  `services/fee_setup.py::money()` — half-up, the way a counter clerk rounds;
  Python's default is banker's rounding and puts a 10% concession a paisa away
  from the printed fee card.
- **Payments allocate to invoice lines, never to invoices.** A balance is a SUM
  over `payment_allocations`, never a stored column. Nothing financial is
  edited: an invoice is voided and reissued, a payment reversed by a contra
  entry.
- **Destructive actions are audited with a reason.** See `services/audit.py`;
  `void`, `status_change` and `delete` refuse to commit without one.

## Traps that have already cost time

- **The test suite builds its schema from the models (`create_all`), not from
  the migrations.** A dropped `server_default` once slipped through this gap.
  `tests/test_migrations.py` covers it — do not delete that test to speed the
  suite up.
- **`BCRYPT_ROUNDS` is 4 in tests, 12 everywhere else.** Never lower it outside
  tests.
- **SQLite returns naive datetimes** even for `timestamptz`; comparing against
  an aware `now` raises.
- **Demo logins changed.** Admission numbers are `2024000001`, not `SPS2024001`.
- **`/admin/settings` is the school's profile and branding.** The setting store
  and module switches are `/admin/configuration`.
- **The Postgres test database is dropped by schema, not by `drop_all`** — a
  leftover v0 table once made the whole suite unable to start.
- **`/public/{school_code}/...` is unauthenticated.** Its 404s are deliberately
  identical across unknown school, suspended school, module off, wrong
  application number and wrong date of birth. Do not make any of them more
  helpful.
- **Local date against UTC midnight is a bug**, and it has already bitten once:
  the office is five and a half hours ahead of the column.
- **`seed.py` runs the real fee and timetable services**, so a defect in either
  breaks seeding rather than only a test. That is on purpose: a seed that
  fabricates rows cannot catch a bug in the code that will produce them.
- **Seeded invoices already carry late fees**, because collection assesses the
  fine before allocating. Do not assume a seeded invoice has a round amount.
- **Money rules are settings, not constants.** The late fee, the sibling
  concession, the due day and the teacher load ceiling all live in
  `core/settings_registry.py`; changing behaviour by editing a number in code
  is the wrong place.

## Working style for this project

- Verify before claiming. Run the thing; do not report from reading the code.
- Commit messages carry the reasoning — why, not just what.
- Show the exact file list before any push.
- Ask before adding a dependency over 100 MB.
