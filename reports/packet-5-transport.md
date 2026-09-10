# Packet 5 — Transport

Branched from `slice/office-feedback`. Transport was on the handoff's "Later"
list; this takes the read-and-operate half of it, not the setup half.

## What I built

| Route | What a clerk does on it | Endpoints |
|---|---|---|
| `/transport` | Sees which routes are running, who rides each one, whether any bus or driver paper has lapsed, and suspends a route or grounds a bus when it must not carry children today | `GET /admin/transport/routes`, `/vehicles`, `/expiring`, `/routes/{id}/students`; `PATCH /admin/transport/routes/{id}/status`, `/vehicles/{id}/status` |

Three cards and a drill-down: **Routes** (code, name, bus, seats taken of
capacity, stop count, status), **Papers expiring** (already-lapsed first, since
the service returns negative `days_left` on purpose), **Buses**. Clicking a
route opens who rides it, by stop, in the order the bus reaches them.

Above the fold: routes running, children riding, and **papers lapsed** — the
one number that means a bus is on the road without valid papers.

## Backend fix included

**Route status changes were audited with a reason the code made up.**
`services/transport.py::set_status` passed
`f"route set to {new_status.value}"`, which restates `after` and answers
nothing. Suspending a route stops children getting to school and the audit log
is the only record of why anyone did it. Grounding a *bus* already demanded a
real reason (`VehicleStatusIn.reason`, min_length 3); suspending the route
those children ride did not.

`reason` is now required and **keyword-only** on `set_status`, so a caller with
no reason to give has to notice rather than inheriting a plausible one. The
seed and six test call sites now state their own (`"seeded demo route"`,
`"test fixture"`). `RouteStatusIn` gained the same `min_length=3` floor the
vehicle route uses.

## The screens.ts entry

Already added (single agent, no orchestrator to hand it to):

```ts
{
  path: "/transport",
  label: "Transport",
  group: "Operations",
  permissions: ["transport.setup.read"],
  modules: ["transport"],
  element: lazy(() => import("./pages/Transport").then((m) => ({ default: m.Transport }))),
},
```

Read off `api/admin/transport.py`: the router carries
`Depends(module_enabled("transport"))` (line 46), and `routes`, `vehicles` and
`expiring` all depend on `reader` = `require_permission("transport.setup.read",
school_wide=True)` (line 48).

**`transport.assignment.read` is deliberately not declared.** It gates only
`GET /admin/transport/routes/{id}/students` — the who-rides-this drill-down —
and is gated at that widget with `<Can>` instead. Declaring it on the screen
would hide the routes, buses and lapsed-papers lists from a setup reader, which
is exactly the over-declaring failure Contract 1 warns about. Four tests in
`screens.test.tsx` pin this, including that the screen opens on
`transport.setup.read` alone.

`Operations` is a new sidebar group. `groupedNav` derives group order from
declaration order, so there was nothing else to register.

## Verification — commands and their real output

```
$ npx tsc --noEmit
0 errors

$ npm test
 Test Files  12 passed (12)
      Tests  51 passed (51)

$ npx vitest run src/screens.test.tsx
 Test Files  1 passed (1)
      Tests  18 passed (18)

$ npm run api:check
schema.d.ts is up to date

$ npm run build
✓ built in 8.94s

$ ../.venv/Scripts/python.exe -m pytest -q
629 passed, 53 warnings in 130.21s (0:02:10)
```

Web went 47 → **51** (four screens-registry tests); backend 628 → **629**
(the route-reason test). `tsc` caught two real
things while building: `to` typed as `string` rather than the union the PATCH
body accepts, and `reason` missing from the generated `RouteStatusIn` until
`npm run api:types` was re-run. That is the typed-request-body layer doing its
job.

## What I clicked, as whom

Against the live API on 8078 with a freshly seeded `sunrise_test`, statuses read
off the browser's own network log.

**As `TRM001` (Rakesh Chandra Dubey, transport_manager) — may:**

| Control | Observed |
|---|---|
| Transport in sidebar | Appears under a new **Operations** group |
| Screen load | 2 routes, 30 children riding, 0 papers lapsed; seats "18 of 40" and "12 of 32"; pollution certificate `16/10/2026` — dd/mm/yyyy, not US order |
| Route row → riders | Children listed by stop in bus order, with class and admission number |
| Suspend route R1 — empty reason | Confirm clicked with the reason blank: **no request fired** |
| Suspend route R1 — real reason | `PATCH /admin/transport/routes/1/status` → **200**; status flipped to `suspended`, button became "Make active", "Routes running" went 2 → 1 |
| Make active R1 | `PATCH .../routes/1/status` → **200**; back to `active`, counter back to 2 |
| Ground UP32AB1234 | `PATCH /admin/transport/vehicles/1/status` → **200**; `vehicles.status` = `grounded` in the database |

The audit rows, which are the point of the backend fix:

```
     actor_label      | entity_id |    action     |                 reason
----------------------+-----------+---------------+----------------------------------------
 Rakesh Chandra Dubey |         1 | status_change | Driver off sick, no cover until Monday
 Rakesh Chandra Dubey |         1 | status_change | Brake fault reported by driver          (vehicle)
 Office Administrator |         2 | status_change | seeded demo route
```

The clerk's own words, against their own name. Before this change the first row
would have read "route set to suspended".

**As `admin@sunrisepublic.edu` — the module gate, which also re-verified Packet 3:**

| Control | Observed |
|---|---|
| Configuration → Transport → Turn off | Confirmation modal, confirmed; the **Transport link disappeared from the sidebar with no page reload** |
| Configuration → Transport → Turn on | Link returned, again without a reload |

That is the first live confirmation of Packet 3's `AuthContext.refresh()`, which
its own report listed as clicked but which I had not verified myself.

**As `counter@sunrisepublic.edu` (Fee Counter Clerk) — may not:**

| Control | Observed |
|---|---|
| Sidebar | No Transport entry |
| Direct navigation to `#/transport` | "You do not have permission — Transport needs `transport.setup.read`, which your role does not hold." Named, not a blank screen. |

State was restored afterwards and checked: both buses `active`, both routes
`active`, transport module on, 10 modules enabled.

## What I did NOT do

- **The setup half of transport is not built**: adding vehicles, fee slabs and
  routes, editing stops, assigning crew, and the assignment desk
  (`POST /admin/transport/assignments`, `PATCH /assignments/{id}`) — so a child
  still cannot be put on a bus from the UI. Eleven of the router's seventeen
  routes have no UI. This screen answers the daily questions; the once-a-term
  setup is a separate packet.
- **`/charges` and `/requests` are not surfaced.** Transport billing goes
  through the ordinary fee run and belongs with the fee screens, not here.
- **The `<Can>` fallback on the riders drill-down was never seen.** No seeded
  role holds `transport.setup.read` without `transport.assignment.read` —
  transport_manager holds both — so the "your role can see the route but not who
  rides it" state is unit-tested only, never rendered. Reported rather than
  faked with another temporary permission grant.
- **Enter-to-submit remains unverified**, as in every prior packet: the harness's
  synthetic Return does not submit forms, which is pre-existing and reproduces
  on the login form.
- **Vehicle statuses other than `grounded`** (`under_maintenance`, `retired`)
  are not settable here, deliberately — they are different operational facts and
  guessing which one a clerk meant would put a wrong reason in the audit log.
  There is also no un-ground control, so restoring the demo bus took an API call.

### One thing I could not reproduce, stated plainly

An early attempt to ground a bus by clicking screen coordinates closed the
dialog without firing any request and without changing the database. Driving the
same dialog by element reference worked correctly every time, and the confirm
button was correctly disabled with `title="A reason is required"` until a reason
was typed. I could not reproduce the coordinate failure deliberately, so I am
recording it as a probable harness artefact rather than claiming an application
defect — but it is written down because "the dialog closed and nothing happened"
is exactly what a real silent-failure bug looks like, and the next person to see
it should not assume it is only the harness.

## Defects found in existing code

1. **No transport route declares a `response_model`** — all seventeen. The
   generated schema types every response `unknown`, so the four shapes in
   `Transport.tsx` are hand-written assertions the compiler cannot check. Each
   one names the service function it was read from. This is the same trap that
   put a live `₹NaN` on the Fees screen, and it is the widest instance of it in
   the codebase.
2. **`PATCH /admin/transport/routes/{id}/crew` and `PUT /routes/{id}/stops`
   change what a bus does and who drives it, and neither takes a reason** —
   worth checking whether they audit at all, in the packet that builds route
   setup.

## Files changed

```
backend/app/services/transport.py       set_status requires a keyword-only reason
backend/app/api/admin/transport.py      RouteStatusIn.reason, passed through
backend/seed.py                         states its own reason
backend/tests/test_transport.py         6 call sites updated; + the reason test
web/src/api/schema.d.ts                 regenerated (npm run api:types)
web/src/screens.ts                      the /transport entry, new Operations group
web/src/screens.test.tsx                + 4 tests pinning the entry
web/src/pages/Transport.tsx             new
reports/packet-5-transport.md           new
```

Nothing pushed. No PR.
