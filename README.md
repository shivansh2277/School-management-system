# Sunrise School Management System

A school management platform with three surfaces over one backend:

| Surface | Users | Form |
|---|---|---|
| Admin dashboard | Office staff | React 18 + Vite SPA |
| Mobile app | Students, parents, teachers | Expo (React Native), one binary, role chosen at login |
| API | Both clients | FastAPI + SQLAlchemy 2.0 over PostgreSQL 16+ (verified on 18.6) |

The design contract is [`docs/BLUEPRINT.md`](docs/BLUEPRINT.md) — it is the source of
truth for the schema, routes, screens and rules. This README covers running it.

**Evidence integrity is a hard rule here.** Every number on every screen comes from a
real query. Where a figure cannot be computed from real data the UI shows an explicit
empty state rather than a placeholder, and trend charts carry only periods that
actually have data.

---

## Cold start

```
git clone <repo> && cd sunrise-school-system
cp backend/.env.example backend/.env
make up && make migrate && make seed
make dev      # terminal 1  -> http://localhost:8000/docs
make web      # terminal 2  -> http://localhost:5173
make mobile   # terminal 3  -> scan the QR code with Expo Go
```

`make` targets assume `python` resolves to an environment with the backend
dependencies installed. To use a virtualenv without activating it:

```bash
make dev PY=backend/.venv/Scripts/python.exe
```

Web and mobile need their dependencies once:

```bash
npm --prefix web install && npm --prefix mobile install
```

### On a physical phone

`localhost` inside the Expo app does not reach your machine. Copy
`mobile/.env.example` to `mobile/.env` and point it at your LAN IP:

```
EXPO_PUBLIC_API_URL=http://192.168.1.7:8000
```

---

## Demo accounts

Printed on both login screens, so a reviewer can get in unaided.

| Role | Login id | Password | Where |
|---|---|---|---|
| Admin | `admin@sunrisepublic.edu` | `Admin@123` | Web dashboard |
| Teacher | `TCH001` | `Teacher@123` | Mobile app |
| Student | `SPS2024001` | `Student@123` | Mobile app |
| Parent | `9876500001` | `Parent@123` | Mobile app |

`TCH001` class-teaches 10-A and teaches it Mathematics; `SPS2024001` is in 10-A;
`9876500001` has two children, so the parent child-switcher is visible on the
default demo account. The API rejects a correct password sent through the wrong
role tab, so an admin cannot sign in on the app and a student cannot sign in on
the dashboard.

---

## Tests

```bash
make test
```

68 tests. `tests/test_scoping.py` covers every deny in the RBAC matrix, and
`tests/test_walkthrough.py` executes the whole cross-role demo — teacher marks
attendance, admin sees it, student sees it, parent sees it, then homework, marks,
fees and notices — end to end against a freshly seeded database. If that file
passes, the demo works.

Against SQLite instead of Postgres (no Docker required):

```bash
TEST_DATABASE_URL=sqlite:///./test.db DATABASE_URL=sqlite:///./dev.db \
  backend/.venv/Scripts/python.exe -m pytest backend/tests -q
```

---

## Shared types

FastAPI publishes the OpenAPI schema; one script turns it into a TypeScript
declaration both clients import:

```bash
make gen-api    # requires `make dev` to be running
```

`packages/api-types/schema.d.ts` is generated but committed, so a fresh clone
type-checks without the backend running. Rename a field in a Pydantic model,
regenerate, and both clients fail to compile at exactly the line that broke.

```bash
npm --prefix web run typecheck
npm --prefix mobile run typecheck
```

---

## Layout

```
backend/    FastAPI app, SQLAlchemy models, services (access scoping lives here), tests, seed
web/        React admin dashboard
mobile/     Expo app - student, parent and teacher tab sets
packages/   generated, committed API types shared by both clients
docs/       BLUEPRINT.md (the contract), API.md, ER-DIAGRAM.md, DEMO-SCRIPT.md
```

Access scoping is enforced in `backend/app/services/scoping.py`, called from the
service layer rather than only at the routes, so a new endpoint cannot skip it.
