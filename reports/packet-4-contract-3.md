# Packet 4 — Contract 3 into Notices, Fees and Exams

Branched from `slice/office-feedback` (`0ca8076`), **not** from `main`, per
`SESSION-HANDOFF-2.md` Part Zero.

## What I built

No new screens. Three existing screens had write controls that rendered for
every role, which is the last of Contract 3's exceptions. All five are now
gated, and the destructive one is confirmed and audited.

| Route | What a clerk does | Endpoint | Permission |
|---|---|---|---|
| `/notices` | Publishes a notice to the board | `POST /admin/notices` | `comms.notice.publish` |
| `/notices` | Takes one off the board, with a reason | `DELETE /admin/notices/{id}` | `comms.notice.publish` |
| `/fees` | Raises a month's invoices | `POST /admin/fees/invoices/generate` | `fees.invoice.generate` |
| `/exams` | Creates an exam | `POST /admin/exams` | `exam.definition.write` |
| `/exams` | Adds a subject paper to one | `POST /admin/exams/{id}/schedule` | `exam.definition.write` (see defect 1) |

Every permission was read off the router itself, not taken from the handoff's
table: `api/admin/notices.py` (POST and DELETE both declare
`comms.notice.publish`), `api/admin/fees.py:112`, `api/admin/exams.py`.

Alongside the gating, two things the contract implies and these pages lacked:

- **The Notices delete now asks for a reason and the backend records it.**
  `services/notices.py::delete` wrote no audit row at all — defect 2 in
  `SESSION-HANDOFF-2.md` Part Three. It now calls `audit.record` with
  `AuditAction.delete`, which `services/audit.py` already refuses to commit
  without a reason, so the dialog's reason is load-bearing rather than
  decorative. The route takes it as a query parameter (`min_length=3`, matching
  `ReasonIn` on the fee routes); `api.del` gained an optional query string, the
  same shape `api.get` already had.
- **A failed `Generate invoices` used to be silent.** The Fees page rendered no
  error for it at all. It now renders `<FormError>`, and the Notices compose
  form puts a 422's field messages next to Title and Body.

## The screens.ts entry the orchestrator must add

**None.** All three screens are already registered and Contract 1 is untouched
by this packet. No route, label, group, permission or module changed.

## Verification — commands and their real output

All run on `slice/office-feedback` + this working tree, against a live API on
8078 (single listener confirmed with `netstat -ano | grep :8078`; a stale
uvicorn from a previous session was holding the port serving older code and was
killed first).

```
$ npx tsc --noEmit
0 errors

$ npm test
 Test Files  12 passed (12)
      Tests  45 passed (45)

$ npm run api:check
schema.d.ts is up to date

$ npm run build
✓ built in 4.25s

$ ../.venv/Scripts/python.exe -m pytest -q
624 passed, 53 warnings in 133.20s (0:02:13)

$ SMOKE_PASSWORD='Admin@123' node smoke.mjs http://127.0.0.1:8078
All smoke checks passed
```

Baseline before any change was **623 backend / 43 web in 11 files**, exactly as
the handoff predicted, and green. The deltas are mine and intended:

- backend 623 → **624**: `test_taking_a_notice_off_the_board_is_audited_with_a_reason`
  in `tests/test_comms.py`.
- web 43 in 11 files → **45 in 12**: `src/pages/Notices.test.tsx`, two tests —
  that the delete sends the reason the clerk typed rather than one of its own,
  and that both controls are disabled without the permission.

### The API, directly

The audit asymmetry, proven at the wire before touching the browser:

```
--- DELETE, no reason ---
{"detail":[{"type":"missing","loc":["query","reason"],"msg":"Field required"}]}
HTTP 422
--- DELETE, reason too short ---
{"detail":[{"type":"string_too_short","loc":["query","reason"],...,"ctx":{"min_length":3}}]}
HTTP 422
--- DELETE, with reason ---
HTTP 204

     actor_label      | entity_id | action |       reason       |       title
----------------------+-----------+--------+--------------------+-------------------
 Office Administrator |         7 | delete | Published in error | Live check notice
```

## What I clicked, as whom

Every one of the five controls, against the running API, as a role that may use
it and a role that may not. Network status codes read off the browser's own
request log.

**As `admin@sunrisepublic.edu` (Office Administrator) — may:**

| Control | Observed |
|---|---|
| Notices → Publish | `POST /admin/notices` → **201 Created**; list refetched, compose form cleared |
| Notices → Delete | Dialog opened. Confirm clicked with an **empty reason first: no request fired at all.** With "Published in error during verification": `DELETE /admin/notices/8?reason=Published%20in%20error%20during%20verification` → **204**, row gone from the list |
| Fees → Generate invoices | `POST /admin/fees/invoices/generate` → **200**, "100 invoice(s) created, 0 already existed." |
| Exams → Create Exam | `POST /admin/exams` → **201**, new exam at the top of the list |
| Exams → Add paper | `POST /admin/exams/5/schedule` → **201**, paper appears in the exam's table |

The audit row from the *browser* delete, not the curl one, carries the words
typed into the dialog:

```
 Office Administrator | 8 | delete | Published in error during verification | Packet 4 verification notice
```

**As `counter@sunrisepublic.edu` (Fee Counter Clerk, `fee_collector`) — may not:**

| Control | Observed |
|---|---|
| Fees → Generate invoices | `disabled=true`, `aria-disabled="true"`, `type="button"`, `title="Your role does not hold fees.invoice.generate"`. **Clicked it: no network request recorded.** |

This role holds `fees.invoice.read` but not `.generate`, so it sees the invoice
list and cannot raise a month's bills — which is the exact split Contract 3 is
about. Notices and Exams do not appear in its sidebar at all.

**As `TRM001` (Rakesh Chandra Dubey, `transport_manager`) — may not:**

| Control | Observed |
|---|---|
| Notices → Publish | `disabled=true`, `title="Your role does not hold comms.notice.publish"`. Verified with the compose form **fully filled in**, so the disabled state is the permission and not the empty-form guard. Clicked: no `POST`. |
| Notices → Delete | Same title, disabled. Clicked: no dialog opened, no `DELETE`. |

**As `TRM001` with `exam.definition.read` temporarily granted — may not:**

| Control | Observed |
|---|---|
| Exams → Create Exam | `disabled=true`, `title="Your role does not hold exam.definition.write"`. Clicked: modal did not open. |
| Exams → Add paper | Same title, disabled. Clicked: no `POST /admin/exams/{id}/schedule`. |

Why the grant was necessary, and what it was: **no seeded account that can sign
into the web app holds `exam.definition.read` without also holding `write`.**
The teacher does (`TCH001`), but the web login authenticates as `admin` and
refuses a teacher outright — "Invalid credentials for this role", observed. So
to see the Exams buttons in their disabled state at all I inserted one row into
`role_permissions` granting `transport_manager` `exam.definition.read`, took the
observations above, and **deleted it again**; a follow-up query confirms zero
`exam%` permissions remain on that role. The seeded permission set is back as it
was. This is stated rather than glossed because the observation is only as good
as the setup that produced it.

## What I did NOT do

- **I did not fix `POST /admin/exams/{id}/schedule`.** The instruction was to
  gate the button and report the route, and that is what happened. The backend
  still accepts that write from anyone holding only `exam.definition.read`.
- **I did not fix the `₹NaN` on the Fees invoice table** (defect 1 below),
  though it is in a file this packet edits. Reasons in that entry — briefly, the
  fix is a field name and choosing the wrong one prints a plausible wrong number
  on a fee screen, which is worse than a visible failure.
- **I did not fix the US-style dates on Notices** (`8/31/2026` for 31 August),
  defect 5 in the handoff. It is a real defect, still open, and out of this
  packet's scope. Note that `asDate` is now defined identically in two files
  (`CollectFees.tsx:93`, `Defaulters.tsx:38`); the fix is to hoist it beside
  `money()` rather than write a third copy.
- **Enter-to-submit is still unverified**, exactly as the previous session left
  it. The browser harness's synthetic Return does not trigger form submission —
  reproduced again here on the login form, which is pre-existing code. Every
  path in this packet was verified by clicking. A human still needs to press
  Enter on the Collect fees search box and the amount field; Part Three rule 3
  remains unproven.
- **The seven screens this packet did not touch were not opened.**

### State the test database was left in

Not pristine, and worth knowing before the next session trusts a figure:

- **100 fee invoices for September 2026** exist because the `Generate invoices`
  verification actually generated them. Real product output, not fixture data.
- The verification notice and the verification exam **were removed** (the notice
  by the feature under test, the exam by SQL, along with its one paper).
- The temporary `role_permissions` grant **was reverted**, confirmed by query.
- To get back to a known state, use the drop-schema/migrate/seed sequence in
  `SESSION-HANDOFF-2.md` Part Zero.

## Defects found in existing code

**1. `/admin/fees/invoices` renders `₹NaN` in the Amount column, on every row.**
Live, on the Fees screen, as admin — visible in the screenshot from the
`Generate invoices` run. This is defect 3 in the handoff's Part Three, now with
a located cause. `Fees.tsx` declares a hand-written `Invoice` type with
`amount: string` and `receipt_no: string | null`. The endpoint returns neither:

```
keys: ['admission_no', 'balance', 'charged', 'class_label', 'discount',
       'due_date', 'enrolment_id', 'id', 'invoice_no', 'lines', 'month',
       'paid', 'payable', 'settled_on', 'status', 'student_id',
       'student_name', 'year']
```

So `money(i.amount)` formats `undefined` and prints `₹NaN`, and the Receipt
column shows `-` unconditionally. Pre-existing — this packet did not touch the
table. It is the second instance of the trap the handoff names: the route has no
`response_model`, so the hand-written type is unchecked and drifted silently,
with `tsc` green throughout.

Not fixed here on purpose. The column is labelled "Amount" and the response
offers `charged`, `payable` and `balance`; those are three different numbers on
a fee screen, and picking the wrong one replaces an obviously broken cell with a
convincingly wrong one. That is the owner's call. The durable fix is a
`response_model` on the route, which would have caught it at compile time.

**2. `POST /admin/exams/{exam_id}/schedule` is a write gated on a read.**
Confirmed live, not by reading the code. The route declares no permission
dependency (`api/admin/exams.py:56-60`) and so inherits the router's
`admin_only`, which is `exam.definition.read` (`api/admin/exams.py:26`). Every
sibling write in that file declares `exam.definition.write`.

As `TCH001`, a teacher holding `['exam.definition.read', 'exam.marks.enter',
'exam.marks.read']` and **not** `exam.definition.write`:

```
--- teacher POST /admin/exams (declares write) ---
HTTP 403
--- teacher POST /admin/exams/4/schedule (declares nothing) ---
{"id":241,...,"class_label":"10-A","subject":"Computer","max_marks":"100"}
HTTP 201
```

A teacher who may only look at the exam calendar scheduled a paper into it. The
probe row was deleted afterwards. The one-line fix is
`dependencies=[Depends(require_permission("exam.definition.write"))]` on that
route, matching every other write in the file. The UI is already gated on the
permission the write *should* need, so fixing the backend will not change what
any role can do from the app — it closes the API to a caller bypassing it.

**3. A tenant-isolation test was passing for the wrong reason after my change,
and I fixed it.** `test_no_delete_or_disable_reaches_another_schools_row`
asserts `DELETE /admin/notices/{id}` returns something other than 200/204 for
another school's notice. Once the route required `reason`, a request without one
returned 422 — still "not 204", so the assertion held while proving nothing
about tenancy. The test now passes `?reason=...` so it exercises the 404 path it
was written for. Flagging it because this class of change is exactly how a
suite quietly stops testing what its name claims.

## Files changed

Backend:

```
backend/app/api/admin/notices.py        DELETE takes `reason`, min_length=3
backend/app/services/notices.py         delete() audits with the reason; takes the actor
backend/tests/test_comms.py             + the audited-delete test
backend/tests/test_tenant_crossing.py   keep the notice case exercising tenancy
```

Web:

```
web/src/api/client.ts                   api.del takes an optional query string
web/src/api/schema.d.ts                 regenerated (npm run api:types)
web/src/pages/Notices.tsx               both writes gated; delete confirmed; 422s per field
web/src/pages/Fees.tsx                  Generate invoices gated; failures now visible
web/src/pages/Exams.tsx                 both writes gated on exam.definition.write
web/src/pages/Notices.test.tsx          new
```

`SESSION-HANDOFF.md` and `reports/README.md` also show as modified/untracked.
**Neither is mine** — both were already in that state before this session began,
as `SESSION-HANDOFF-2.md` Part Zero records.

Nothing pushed. No PR opened.
