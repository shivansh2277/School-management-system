# Sunrise School Management System — Complete Build Specification (v0)

**Status:** v0 implemented — backend, admin dashboard and Expo app build and pass the §13 walkthrough
**Date:** 2026-09-01
**Owner:** Shivansh Shukla (`shiv.dev2911@gmail.com`)
**Companion artifact:** https://claude.ai/code/artifact/c7518b5f-f84d-42ac-b22c-b128523cf2cd

---

## 0. How to use this document

This file is the **single source of truth**. It is written so that an agent or developer
starting from a cold clone, with no memory of the conversation that produced it, can build
the entire system without asking further questions.

If you are an AI assistant starting fresh, your instructions are:

1. Read this document end to end before writing any code.
2. Build in the order given in §16. Do not skip ahead.
3. Where this document specifies a name — table, column, enum value, route, file path,
   env var — use that exact name. The clients and the backend are wired to each other
   through these names.
4. Where this document is silent, choose the smallest thing that works and record the
   choice in §19 (Open items).
5. Do not add features that are not in this document. §18 lists what is deliberately absent
   and must stay absent.

### Project context an agent cannot infer from the code

- This is a **template product**, not a one-off. It will be customised and re-deployed for
  real schools. Treat it as production code, not a throwaway demo.
- The owner is a 3rd-year B.Tech CSE student building this as a portfolio and client
  demo piece. It will be shown to schools and to industry reviewers on GitHub.
- **Evidence integrity is a hard requirement.** Nothing on any screen may be fabricated.
  Every displayed number must be derived from an actual database query. If a statistic
  cannot be computed from real data, the UI omits it rather than inventing it. This rule
  overrides visual completeness — an empty state is correct, a fake percentage is not.
- The system is Indian-context: ₹ currency, Indian names, Indian school conventions
  (classes 1–12 with sections, terms, admission numbers).
- v0 will be run locally first, then pushed to GitHub as a public repository.

---

## 1. What the system is

A school management platform with three surfaces sharing one backend:

| Surface | Users | Form |
|---|---|---|
| **Admin dashboard** | School management / office staff | Web (React SPA) |
| **Mobile app** | Students, parents, teachers | React Native via Expo — one binary, role chosen at login |
| **API** | Both of the above | FastAPI over PostgreSQL |

### The single most important thing to get right

The **cross-role data loop** must work end to end:

```
Teacher marks attendance on the mobile app
        ↓ (same database row)
Admin dashboard attendance percentage changes
        ↓
Student sees their own attendance record
        ↓
Parent sees that same child's attendance record
```

The same loop exists for homework, marks and notices. A reviewer will be walked through
these loops live. If they work, the demo succeeds; if any link is mocked, it fails.

---

## 2. Locked decisions

These were decided during design. Do not re-litigate them while building.

| # | Decision | Rationale |
|---|---|---|
| D1 | **Single tenant** — one deployment per school | Multi-tenancy would put a `school_id` predicate on every query and double the access-control test surface for zero v0 benefit |
| D2 | **Attendance is once per day**, not per period | Matches most Indian schools; enforced by a DB unique constraint |
| D3 | **Letter grades, no class rank** | Rank is socially loaded and hard to defend in a demo |
| D4 | **Monthly fee billing**, not per term | Confirmed requirement |
| D5 | **Simulated payment** — no real gateway | A real gateway adds compliance and secret keys to a demo |
| D6 | **Text-only homework answers** in v0 | File upload/storage is the largest complexity jump for the least demo value |
| D7 | **In-app notice feed, not push notifications** | Push needs device tokens and a delivery service |
| D8 | **Timetable is seeded and read-only** | A conflict-checking timetable editor is a project of its own |
| D9 | **No fabricated trend indicators** | See evidence-integrity rule in §0 |
| D10 | **Light mode only, English only** | Scope control |
| D11 | One `users` table for all four roles | Authentication becomes one code path instead of four |
| D12 | Access scoping enforced in the **service layer**, not only at routes | A new endpoint cannot accidentally skip it |

---

## 3. Technology stack

| Layer | Choice | Version |
|---|---|---|
| Language (backend) | Python | 3.12+ — **verified on 3.13.7** |
| Web framework | FastAPI | ≥ 0.115 |
| ORM | SQLAlchemy | 2.0 (declarative, typed `Mapped[]` style) |
| Migrations | Alembic | latest |
| Validation | Pydantic | v2 |
| Database | PostgreSQL | 16+ — **verified on 18.6, installed natively (no Docker)**. `docker-compose.yml` still pins `postgres:16` as the containerised default |
| DB driver | psycopg | 3 (`psycopg[binary]`) |
| Auth | `python-jose[cryptography]` for JWT, `passlib[bcrypt]` for hashing | — |
| PDF | ReportLab | latest |
| Backend tests | pytest, pytest-asyncio, httpx | — |
| Web framework (client) | React | 18 |
| Web build | Vite | 5 |
| Web styling | Tailwind CSS | 3 |
| Web data layer | TanStack Query | 5 |
| Web routing | React Router | 6 |
| Web charts | Recharts | 2 |
| Mobile | Expo SDK | 51+ — **verified on 54.0.37**, running in Expo Go for SDK 54 on a physical Android device (see §19 #14). React 19.1 / React Native 0.81 come with it |
| Mobile routing | Expo Router | latest — 6.x on SDK 54 |
| Mobile data layer | TanStack Query | 5 |
| Shared types | openapi-typescript | latest |
| Language (clients) | TypeScript | 5 |

**Why Expo and not bare React Native:** a reviewer can open the app on their own phone by
scanning a QR code with Expo Go, with no Android Studio setup.

---

## 4. Architecture

```
                     +------------------------+
   Web (admin)   --->|                        |
                     |  FastAPI               |--->  PostgreSQL
   Expo (mobile) --->|  SQLAlchemy 2.0        |
                     |  JWT auth + RBAC       |
                     +------------------------+
                                |
                          /openapi.json
                                |
                   openapi-typescript (build step)
                                |
                      packages/api-types/schema.d.ts
                          ^                ^
                         web            mobile      <-- INTENDED, NOT BUILT (§19 #20)
```

One FastAPI service is the single source of truth. Both clients are stateless readers of it
and talk to nothing else.

### Type sharing between web and mobile

FastAPI publishes an OpenAPI schema derived from the Pydantic response models. One npm
script regenerates a shared TypeScript declaration file from it:

```
npx openapi-typescript http://localhost:8000/openapi.json -o packages/api-types/schema.d.ts
```

`packages/api-types/schema.d.ts` is **generated but committed**, so a fresh clone
type-checks without the backend running. `packages/api-types/openapi.json` is committed
alongside it so the types can be regenerated without starting the server.

Each client has one thin `apiClient` wrapper (fetch + bearer token + base URL from env).
No other HTTP code exists in either client.

> **Not implemented in v0 — do not describe this as working.** The intended strategy was
> that both clients import `schema.d.ts`, so renaming a Pydantic field would break both
> clients at compile time. **Neither client imports it.** `web/tsconfig.json` only lists the
> folder under `include`; `mobile/tsconfig.json` does not reference it at all. Both clients
> hand-write their response types — see the `Stats` type at the top of
> `web/src/pages/Dashboard.tsx`. A backend rename therefore breaks the clients **silently at
> runtime**, not at compile time.
>
> Wiring it up means typing the responses in `web/src/api/client.ts` and
> `mobile/src/api/client.ts` from `schema.d.ts` (and adding the path to
> `mobile/tsconfig.json`). Until that is done, the file is generated but unused. See §19 #20.

---

## 5. Repository layout

```
sunrise-school-system/
├── backend/
│   ├── app/
│   │   ├── main.py                  FastAPI app, router registration, CORS
│   │   ├── core/
│   │   │   ├── config.py            pydantic-settings, reads .env
│   │   │   ├── security.py          hash_password, verify_password, create_token, decode_token
│   │   │   ├── db.py                engine, SessionLocal, Base, get_db dependency
│   │   │   └── deps.py              get_current_user, require_role(...)
│   │   ├── models/                  one module per domain area, all importing Base
│   │   │   ├── user.py              User, Student, Teacher, Parent, ParentStudent
│   │   │   ├── academic.py          ClassSection, Subject, ClassSubjectTeacher, TimetableSlot
│   │   │   ├── ops.py               Attendance, Homework, HomeworkSubmission, Notice
│   │   │   ├── assessment.py        Exam, ExamSchedule, Mark, GradeBand
│   │   │   └── fees.py              FeeStructure, FeeInvoice, FeePayment, SchoolSettings
│   │   ├── schemas/                 Pydantic models, mirrors models/
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── admin/               students, teachers, classes, notices, exams, fees, stats
│   │   │   ├── teacher/             classes, attendance, homework, marks, announcements
│   │   │   ├── student/             dashboard, timetable, homework, attendance, results
│   │   │   └── parent/              children, attendance, homework, results, fees
│   │   ├── services/                business logic + ACCESS SCOPING (see §9)
│   │   │   ├── scoping.py           the four scoping helpers — read this first
│   │   │   ├── attendance.py
│   │   │   ├── homework.py
│   │   │   ├── assessment.py
│   │   │   ├── fees.py
│   │   │   ├── notices.py
│   │   │   └── stats.py
│   │   └── pdf/receipt.py           ReportLab fee receipt
│   ├── alembic/versions/
│   ├── seed.py                      idempotent demo data (see §15)
│   ├── tests/
│   │   ├── conftest.py              test DB, client fixture, role-token fixtures
│   │   ├── test_auth.py
│   │   ├── test_scoping.py          NEGATIVE TESTS — written before features
│   │   ├── test_attendance.py
│   │   ├── test_homework.py
│   │   ├── test_assessment.py
│   │   ├── test_fees.py
│   │   └── test_stats.py
│   ├── pyproject.toml
│   └── .env.example
├── web/
│   ├── src/
│   │   ├── main.tsx, App.tsx
│   │   ├── api/client.ts            fetch wrapper, token handling
│   │   ├── auth/                    AuthContext, ProtectedRoute, LoginPage
│   │   ├── layout/                  Sidebar, Topbar, Shell
│   │   ├── pages/                   Dashboard, Students, Teachers, Classes, Attendance,
│   │   │                            Exams, Assignments, Fees, Notices, Settings
│   │   ├── components/              StatCard, DataTable, Donut, Pill, Modal, FormField
│   │   └── theme.ts                 design tokens (see §14)
│   ├── index.html, vite.config.ts, tailwind.config.js
│   └── .env.example                 VITE_API_URL
├── mobile/
│   ├── app/                         Expo Router
│   │   ├── index.tsx                role picker + login
│   │   ├── (student)/               _layout.tsx + 7 tabs
│   │   ├── (parent)/                _layout.tsx + 8 tabs
│   │   └── (teacher)/               _layout.tsx + 8 tabs
│   ├── src/api/client.ts
│   ├── src/auth/AuthContext.tsx
│   ├── src/components/
│   ├── src/theme.ts                 same tokens as web
│   ├── app.json
│   └── .env.example                 EXPO_PUBLIC_API_URL
├── packages/api-types/schema.d.ts   generated, committed
├── docs/
│   ├── BLUEPRINT.md                 this file
│   ├── ER-DIAGRAM.md
│   ├── API.md
│   ├── DEMO-SCRIPT.md
│   └── CUSTOMISATION.md             written only after v0 is signed off
├── docker-compose.yml               postgres:16 + adminer
├── Makefile
└── README.md
```

---

## 6. Configuration and commands

### `backend/.env.example`

```
DATABASE_URL=postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise
TEST_DATABASE_URL=postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test
JWT_SECRET=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
CORS_ORIGINS=http://localhost:5173,http://localhost:8081
SCHOOL_NAME=Sunrise Public School
ACADEMIC_YEAR=2025-26
```

`web/.env.example` → `VITE_API_URL=http://localhost:8000`
`mobile/.env.example` → `EXPO_PUBLIC_API_URL=http://localhost:8000`

> On a physical phone, `localhost` will not reach the host machine. The mobile README must
> tell the user to set `EXPO_PUBLIC_API_URL` to their machine's LAN IP, e.g.
> `http://192.168.1.7:8000`.

### `Makefile` targets

| Target | Does |
|---|---|
| `make up` | `docker compose up -d` — Postgres + Adminer |
| `make migrate` | `alembic upgrade head` |
| `make seed` | drop-and-rebuild demo data (idempotent) |
| `make dev` | run FastAPI with `--reload` on :8000 |
| `make web` | `npm --prefix web run dev` on :5173 |
| `make mobile` | `npx expo start --prefix mobile` |
| `make test` | `pytest` against `TEST_DATABASE_URL` |
| `make gen-api` | regenerate `packages/api-types/schema.d.ts` |

### Cold-start sequence (must appear verbatim in the README)

```
git clone <repo> && cd sunrise-school-system
cp backend/.env.example backend/.env
make up && make migrate && make seed
make dev      # terminal 1  → http://localhost:8000/docs
make web      # terminal 2  → http://localhost:5173
make mobile   # terminal 3  → scan QR with Expo Go
```

---

## 7. Data model

21 tables. All tables have `id BIGSERIAL PRIMARY KEY`, `created_at TIMESTAMPTZ NOT NULL
DEFAULT now()`, and where mutable, `updated_at TIMESTAMPTZ`.

### 7.1 Enums

```python
UserRole        = admin | teacher | parent | student
AttendanceStatus= present | absent | leave
NoticeAudience  = all | students | parents | teachers | class
InvoiceStatus   = pending | paid | overdue
Gender          = male | female | other
DayOfWeek       = mon | tue | wed | thu | fri | sat
```

### 7.2 Identity and people

**`users`** — one table for all four roles.

| Column | Type | Notes |
|---|---|---|
| id | bigserial PK | |
| role | UserRole | |
| login_id | varchar(64) | **UNIQUE, NOT NULL.** Holds email (admin), employee_id (teacher), admission_no (student) or mobile (parent) |
| password_hash | varchar(255) | bcrypt |
| full_name | varchar(120) | |
| email | varchar(160) | nullable |
| phone | varchar(20) | nullable |
| photo_url | text | nullable — v0 stores a seeded avatar URL or null |
| is_active | boolean | default true |

Index on `(role, login_id)`.

**`students`**

| Column | Type | Notes |
|---|---|---|
| user_id | FK users, UNIQUE, NOT NULL | |
| admission_no | varchar(32) | UNIQUE. Format `SPS2024001` |
| class_section_id | FK class_sections | |
| roll_no | int | UNIQUE within class_section |
| dob | date | |
| gender | Gender | |
| address | text | |
| admission_date | date | |

**`teachers`** — user_id (FK, unique), employee_id varchar(16) unique (`TCH001`),
qualification varchar(120), joining_date date.

**`parents`** — user_id (FK, unique), occupation varchar(80) nullable.

**`parent_student`** — parent_id FK, student_id FK, relation varchar(20)
(`father`/`mother`/`guardian`). **UNIQUE(parent_id, student_id).**
This join table is what makes the sibling switcher work; a parent row may link to N students.

### 7.3 Academic structure

**`class_sections`** — class_name varchar(8) ("8","9","10"), section varchar(4) ("A"),
class_teacher_id FK teachers nullable, academic_year varchar(9) ("2025-26").
**UNIQUE(class_name, section, academic_year).** Display label is `{class_name}-{section}`.

**`subjects`** — name varchar(60), code varchar(12) UNIQUE.

**`class_subject_teacher`** — class_section_id, subject_id, teacher_id.
**UNIQUE(class_section_id, subject_id).** This table defines *who teaches what, where*, and
is the basis of teacher scoping.

**`timetable_slots`** — class_section_id, day_of_week DayOfWeek, period_no int,
start_time time, end_time time, subject_id, teacher_id, room varchar(20).
**UNIQUE(class_section_id, day_of_week, period_no).**

### 7.4 Daily operations

**`attendance`**

| Column | Type | Notes |
|---|---|---|
| student_id | FK students | |
| date | date | |
| status | AttendanceStatus | |
| marked_by | FK teachers | |
| remarks | varchar(200) | nullable |

**UNIQUE(student_id, date)** — this constraint is what enforces D2 (once per day). Do not
enforce it only in application code. Index on `(date)` and `(student_id, date)`.

**`homework`** — class_section_id, subject_id, teacher_id, title varchar(160),
description text, assigned_date date, due_date date.

**`homework_submissions`** — homework_id, student_id, answer_text text,
submitted_at timestamptz. **UNIQUE(homework_id, student_id).**

> There is no `status` column. A row exists → submitted. No row → not submitted.
> Pending counts are computed as (students in class) − (submission rows).

**`notices`** — title varchar(160), body text, audience NoticeAudience,
class_section_id FK nullable (required only when audience = `class`),
published_by FK users, published_at timestamptz.

### 7.5 Assessment

**`exams`** — name varchar(120) ("Term 1 — Unit Test 1"), term varchar(20) ("Term 1"),
start_date date, end_date date.

**`exam_schedule`** — exam_id, class_section_id, subject_id, exam_date date,
start_time time, max_marks numeric(5,2).
**UNIQUE(exam_id, class_section_id, subject_id).**

**`marks`** — exam_schedule_id, student_id, marks_obtained numeric(5,2),
entered_by FK teachers. **UNIQUE(exam_schedule_id, student_id).**
CHECK `marks_obtained >= 0`. Application must reject `marks_obtained > max_marks`.

**`grade_bands`** — min_percent numeric(5,2), grade varchar(4). Seeded:

| min_percent | grade |
|---|---|
| 91 | A1 |
| 81 | A2 |
| 71 | B1 |
| 61 | B2 |
| 51 | C1 |
| 41 | C2 |
| 33 | D |
| 0 | E |

Grade is **computed at read time** from percentage against this table, never stored.

### 7.6 Fees

**`fee_structures`** — class_name varchar(8) UNIQUE, monthly_amount numeric(10,2).

**`fee_invoices`** — student_id, month int (1–12), year int, amount numeric(10,2),
due_date date, status InvoiceStatus. **UNIQUE(student_id, month, year).**

**`fee_payments`** — invoice_id FK UNIQUE, amount numeric(10,2), paid_at timestamptz,
method varchar(20) default `'simulated'`, txn_ref varchar(40), receipt_no varchar(24) UNIQUE.

Receipt number format: `SPS/RCP/{year}/{zero-padded sequence}` e.g. `SPS/RCP/2026/000017`.
Transaction reference format: `SIM-{uuid4 hex, first 12 chars, uppercase}`.

**`school_settings`** — single row (id always 1): name, address, city, phone, email,
logo_url, primary_color, academic_year. **Everything school-specific on any screen reads
from here**, never from a hardcoded string. This is what makes D1 (configure-and-redeploy)
work.

---

## 8. Domain rules

These are the behaviours that are not obvious from the schema. Implement them in
`app/services/`, and cover each with a test.

### Attendance
- A teacher may mark attendance only for a class section they class-teach or teach a subject in.
- Marking is a **bulk upsert** for one `(class_section, date)`: the payload contains every
  student in the section. Re-submitting the same date overwrites (upsert on the unique key).
- Attendance may not be marked for a future date → `400`.
- Attendance percentage = `present / (present + absent + leave) * 100`, rounded to 1 dp.
  Leave counts against presence. State this in the UI label so it is unambiguous.

### Homework
- A teacher may create homework only for a `(class_section, subject)` pair they own in
  `class_subject_teacher`.
- `due_date >= assigned_date`, else `400`.
- A student may submit only to homework assigned to their own class section.
- Submitting twice **updates** the existing row (upsert) and refreshes `submitted_at`.
- Submission after `due_date` is allowed and recorded — v0 does not lock late submissions,
  but the teacher's list shows a `Late` flag computed from `submitted_at > due_date`.
- Per D6 the answer is text only. `answer_text` must be non-empty after trim → `422`.

### Marks
- A teacher may enter marks only for an `exam_schedule` whose `(class_section, subject)`
  they own.
- Entry is bulk for one `exam_schedule_id`; payload is a list of `(student_id, marks)`.
- Reject `marks_obtained > max_marks` → `422` naming the offending student.
- Report card for a student and exam: rows of (subject, marks_obtained, max_marks,
  percentage, grade), plus total obtained, total max, overall percentage, overall grade.
- Absent from an exam = no `marks` row. Report card shows `—`, and that subject is excluded
  from the total. Do not treat it as zero.

### Notices
- Audience filtering on read:
  - `all` → visible to every role
  - `students` / `parents` / `teachers` → that role only
  - `class` → students of that `class_section_id`, and parents of those students
- **A teacher may publish only `audience = class`, and only for a section they teach.**
  The school-wide values (`all`, `students`, `parents`, `teachers`) are admin-only. A
  teacher attempting any other audience gets `403`.

  *Why the restriction:* a `students` notice by definition reaches every student in the
  school, and there is no per-section variant of it. Allowing a teacher to publish one
  would silently broadcast beyond their scope. `class` already delivers to the students of
  that section **and** their parents, which is what a teacher actually needs.

### Fees
- Invoice generation is per `(month, year)` across all active students: amount is looked up
  from `fee_structures` by the student's `class_name`. **Idempotent** — re-running for the
  same month must not create duplicates (rely on the unique key, skip existing).
- `status` is derived on read when `pending` and `due_date < today` → present as `overdue`.
  Persist the transition when the invoice list is generated; never show `pending` for a past
  due date.
- Payment (`POST /parent/fees/{id}/pay`): create a `fee_payments` row, generate `txn_ref`
  and `receipt_no`, set invoice `status = paid`. Reject if already paid → `409`.
- The receipt PDF is generated on demand from the invoice + payment + school settings. It
  must contain: school name and address, receipt no, date, student name, admission no,
  class-section, billing month, amount in figures **and words**, payment mode, and a
  "system generated receipt" footnote.

### Dashboard statistics (all live SQL — see §0 evidence rule)
- Total students = count of active students.
- Total teachers = count of active teachers.
- Total classes = count of class sections in the current academic year.
- Fees collected = `SUM(fee_payments.amount)` for the current academic year.
- Attendance overview = counts by status over the current month.
- Performance distribution = each student's average percentage over the latest exam,
  bucketed: Excellent ≥ 80, Good 60–79, Average 40–59, Needs improvement < 40.
- Top performers = top 3 students by average percentage in the latest exam.
- Today's schedule = `timetable_slots` for today's `day_of_week`, ordered by period.
- **Trend sparklines / percentage deltas appear only where a real prior period exists**
  (attendance by day, fee collection by month). Where there is no comparable history,
  render the figure with no trend element. Never fabricate one.

---

## 9. Authentication and access control

### Login

`POST /auth/login` with `{ role, login_id, password }`. The `role` field selects which tab
the user came from and must match `users.role`, so a student cannot log in through the
teacher tab even with correct credentials.

Response: `{ access_token, refresh_token, token_type: "bearer", user: {...} }`.

JWT claims: `sub` (user id), `role`, `exp`. Access token 24 h (demo setting), refresh 30 d.
Passwords hashed with bcrypt via passlib. Every role can change their own password.

### Scoping — implement in `app/services/scoping.py`

Four helpers, used by every service function that touches student-owned data:

```python
def student_id_for(user) -> int                    # student's own record
def child_ids_for(user) -> list[int]               # via parent_student
def class_section_ids_for(user) -> list[int]       # teacher: class-teaches OR teaches a subject in
def assert_can_read_student(user, student_id)      # raises 403
```

### RBAC matrix

| Resource | Admin | Teacher | Parent | Student |
|---|---|---|---|---|
| Students (list/create/edit) | full | read, own sections only | — | — |
| Teachers, Classes, Subjects | full | read own | — | — |
| Attendance | read all, no write | write + read own sections | read own children | read self |
| Homework | read all | full, own sections + subjects | read own children | read own class, submit |
| Exams / schedule | full | read own | — | read own class |
| Marks | read all | write + read own sections + subjects | read own children | read self |
| Notices | publish any audience | publish `class` only, own sections only | read (audience filtered) | read (audience filtered) |
| Fees | full, generate invoices | — | read own children, pay | — |
| Dashboard stats | full | own sections summary | own children summary | own summary |

**Every deny in that matrix gets a negative test.** See §17.

---

## 10. API specification

Base URL `/`. All routes except `/auth/login` and `/auth/refresh` require
`Authorization: Bearer <token>`.

Standard error shape: `{ "detail": "<message>" }`.
Codes used: `400` invalid request · `401` missing/expired token · `403` out of scope ·
`404` not found · `409` conflict (already paid, duplicate) · `422` validation.

**Conventions that apply to every route:**

- Any route taking `?page` returns
  `{ "items": [...], "total": int, "page": int, "page_size": int }`.
  Default `page_size` is 25. Routes without `page` return a bare array.
- Dates are ISO `YYYY-MM-DD`; timestamps are ISO 8601 with timezone. Money is a
  string-serialised decimal with 2 dp (never a float), and clients format the ₹ symbol.
- IDs are integers. A response that names a person always carries both `id` and
  `full_name`, so no client has to make a second call to render a row.
- The web dashboard sends `role: "admin"` at login. Admin cannot log in on the mobile app,
  and the three mobile roles cannot log in on the web dashboard.

### Auth

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| POST | `/auth/login` | `{role, login_id, password}` | tokens + user |
| POST | `/auth/refresh` | `{refresh_token}` | new access token |
| GET | `/auth/me` | — | current user + role-specific profile block |
| POST | `/auth/change-password` | `{old_password, new_password}` | `204` |

`/auth/me` returns the role profile inline, so a client needs one call at boot:
student → admission_no, class_section label, roll_no; teacher → employee_id, sections;
parent → children list `[{id, name, class_label, admission_no}]`; admin → nothing extra.

### Admin

```
GET    /admin/dashboard/stats
       → { totals:{students,teachers,classes,fees_collected},
           attendance:{present,absent,leave,percent},
           performance:{excellent,good,average,needs_improvement},
           top_performers:[{student_id,name,class_label,average_percent}],
           recent_notices:[...],
           today_schedule:[{period,time,class_label,subject,teacher,room}],
           fee_trend:[{month,collected}]  # only months with data
         }

GET    /admin/students?class_section_id&q&page        list + filter + search
POST   /admin/students                                creates user + student in one tx
GET    /admin/students/{id}
PATCH  /admin/students/{id}
DELETE /admin/students/{id}                           soft delete → users.is_active=false

GET    /admin/teachers        POST /admin/teachers    PATCH/DELETE /admin/teachers/{id}
GET    /admin/classes         POST /admin/classes     PATCH /admin/classes/{id}
GET    /admin/subjects                                read-only (D8-adjacent, seeded)
GET    /admin/timetable?class_section_id              read-only

GET    /admin/attendance/summary?from&to&class_section_id
GET    /admin/attendance?class_section_id&date        roll for one day

GET    /admin/exams           POST /admin/exams
POST   /admin/exams/{id}/schedule                     add a subject paper
GET    /admin/exams/{id}/schedule

GET    /admin/notices         POST /admin/notices     DELETE /admin/notices/{id}

GET    /admin/fees/structures
GET    /admin/fees/invoices?month&year&status&class_section_id
POST   /admin/fees/invoices/generate  {month, year}   idempotent
GET    /admin/fees/collection?year                    per-month collected vs billed
```

`POST /admin/students` body: `{full_name, admission_no, class_section_id, roll_no, dob,
gender, address, admission_date, phone, email, password, parent:{full_name, phone,
relation, occupation, password} | parent_id}` — creating a student may either create a new
parent account or link to an existing one (this is how siblings are attached).

### Teacher

```
GET    /teacher/classes                               sections + subjects they own
GET    /teacher/timetable                             their own week

GET    /teacher/attendance?class_section_id&date      roll sheet, pre-filled if already marked
POST   /teacher/attendance
       { class_section_id, date, entries:[{student_id, status, remarks?}] }   bulk upsert

GET    /teacher/homework?class_section_id&subject_id
POST   /teacher/homework    { class_section_id, subject_id, title, description, due_date }
PATCH  /teacher/homework/{id}
DELETE /teacher/homework/{id}
GET    /teacher/homework/{id}/submissions
       → [{student_id, name, roll_no, submitted:bool, submitted_at, late:bool, answer_text}]

GET    /teacher/exams                                 papers scheduled for their sections
GET    /teacher/marks?exam_schedule_id                roster with existing marks
POST   /teacher/marks  { exam_schedule_id, entries:[{student_id, marks_obtained}] }

POST   /teacher/announcements  { title, body, class_section_id }
       audience is forced to "class"; any other value → 403 (see §8 Notices)
GET    /teacher/announcements                         their own published notices
```

### Student

```
GET    /student/dashboard
       → { attendance_percent, homework_pending, next_exam, latest_result_percent,
           recent_notices, today_schedule }
GET    /student/timetable
GET    /student/attendance?month&year                 day-wise + monthly summary
GET    /student/homework?status=pending|submitted|all
POST   /student/homework/{id}/submit   { answer_text }
GET    /student/exams                                 upcoming schedule
GET    /student/results                               list of exams
GET    /student/results/{exam_id}                     full report card
GET    /student/notices
GET    /student/profile
```

### Parent

```
GET    /parent/children                               drives the child switcher
GET    /parent/children/{student_id}/summary
GET    /parent/children/{student_id}/attendance?month&year
GET    /parent/children/{student_id}/homework         submitted vs pending counts + list
GET    /parent/children/{student_id}/results
GET    /parent/children/{student_id}/results/{exam_id}
GET    /parent/children/{student_id}/profile
GET    /parent/fees?student_id                        invoice list
POST   /parent/fees/{invoice_id}/pay                  simulated → 200 with receipt_no
GET    /parent/fees/{invoice_id}/receipt.pdf          application/pdf
GET    /parent/notices
```

Every `/parent/children/{student_id}/*` route calls `assert_can_read_student` first.

---

## 11. Admin dashboard — screen specification

Layout: fixed 240 px indigo sidebar, top bar with search and profile menu, content area on a
light grey ground. Light mode only.

| Screen | Contents |
|---|---|
| **Dashboard** | 4 stat cards (Total Students, Total Teachers, Total Classes, Fees Collected ₹) · Student Performance donut (4 buckets, legend with counts and %) · Attendance Overview donut (present/absent/leave, big % in the centre) · Recent Notices list · Top 3 Performers with avatar, class, average % · Today's Schedule as a time-rail list |
| **Students** | Searchable, class-filterable table: photo/initials, name, admission no, class-section, roll no, parent name, phone. Row click → detail drawer (profile, attendance %, latest result, fee status). "Add Student" modal creates the student **and** their parent login in one transaction |
| **Teachers** | Table: employee id, name, qualification, subjects taught, sections, class-teacher-of. Add/edit modal |
| **Classes** | Card grid per section: label, class teacher, student count, subject chips. Detail → student roster + timetable (read only) |
| **Attendance** | Date picker + class selector → read-only roll sheet with status pills; below it, a monthly summary bar per section. Admin does not mark attendance (see §9 matrix) |
| **Exams** | Exam list → create exam → add subject papers (class, subject, date, time, max marks). Per-paper marks-entry status: entered / pending |
| **Assignments** | All homework across sections: title, subject, class, teacher, due date, submitted-count / total. Row click → submission list |
| **Fees** | Month/year selector · "Generate invoices" action (idempotent, reports created vs skipped) · invoice table with status pills · collection summary: billed, collected, outstanding, plus a monthly collected bar chart built only from months that have data |
| **Notices** | Compose (title, body, audience selector, class picker when audience = class) · published list with audience chips |
| **Settings** | School settings form (name, address, contact, academic year, logo URL, primary colour), grade bands table, fee structure per class. This screen is what makes the template re-skinnable |

Empty states are explicit and honest: "No attendance marked for this date yet." Never an
empty chart pretending to be data.

---

## 12. Mobile app — screen specification

One Expo app. The login screen shows three role tabs — **Student · Parent · Teacher** — and
the demo credentials for each, so a reviewer can get in unaided. After login the app routes
to the matching tab group. (Admin logs in on the web, not the app.)

### Student — 7 tabs

| Tab | Contents |
|---|---|
| Dashboard | Greeting with name and class · attendance % ring · pending homework count · next exam · latest result % · latest notices |
| Timetable | Day selector Mon–Sat, period list with subject, teacher, time, room |
| Homework | Pending / Submitted filter · card list with subject chip, title, due date, overdue flag · tap → detail with description and answer box → Submit |
| Attendance | Month calendar with per-day colour, plus present/absent/leave counts and % |
| Exams & Results | Upcoming exam schedule · past exams → report card (subject rows, marks/max, %, grade; totals row) |
| Notifications | Audience-filtered notice feed, newest first |
| Profile | Name, admission no, class, roll no, DOB, address, parent contact · change password · logout |

### Parent — 8 tabs

Header carries a **child switcher** when the parent has more than one child; every tab
reflects the selected child. Selection persists for the session.

| Tab | Contents |
|---|---|
| Dashboard | Selected child's attendance %, homework submitted vs pending, latest result %, fee dues badge, recent notices |
| Child Profile | Full student profile + class teacher contact |
| Attendance | Same month calendar as the student view, read-only |
| Homework | Submitted vs pending counts and the list, read-only (D-rule: parents do not submit) |
| Results | Exam list → full report card |
| Fees | Invoice list with status pills · **Pay Now** on pending/overdue → simulated confirm sheet → success → status flips to Paid · **Download Receipt** on paid |
| Notifications | Audience-filtered feed |
| Profile | Parent's own profile, linked children, change password, logout |

### Teacher — 8 tabs

| Tab | Contents |
|---|---|
| Dashboard | Today's periods · sections taught · pending marks entry · pending homework reviews |
| My Classes | Section cards → student roster |
| Attendance | Class + date → roll sheet with Present/Absent/Leave toggles, "Mark all present" shortcut, Save (bulk upsert). Re-opening a marked date pre-fills |
| Homework | Their assignments list · create form (class, subject, title, description, due date) · tap → submission list with submitted/not and late flags |
| Results | Their exam papers → marks entry roster with max-marks validation inline → Save |
| Announcements | Compose scoped to their sections · their published list |
| Timetable | Their own weekly schedule |
| Profile | Employee id, qualification, subjects, sections · change password · logout |

---

## 13. Cross-role acceptance walkthrough

This is the demo script and also the definition of "it works". Build until every step passes
against a freshly seeded database.

1. Log in as **teacher** `TCH001` → Attendance → 10-A → today → mark 2 students absent → Save.
2. Log in as **admin** on web → Dashboard → attendance overview reflects those 2 absences.
3. Log in as **student** `SPS2024001` (one of the absent) → Attendance → today shows Absent.
4. Log in as **parent** `9876500001` → that child → Attendance → same absence visible.
5. As **teacher** → Homework → create for 10-A / Mathematics, due tomorrow.
6. As **student** → Homework → the new item is Pending → open → type an answer → Submit.
7. As **teacher** → that homework → submissions → that student shows Submitted.
8. As **parent** → Homework → submitted count incremented.
9. As **admin** → Exams → create "Term 1 — Unit Test 2" → add a Mathematics paper for 10-A.
10. As **teacher** → Results → that paper → enter marks → Save. Entering above max is rejected.
11. As **student** → Results → report card shows the subject, %, and grade.
12. As **parent** → Results → same report card.
13. As **admin** → Fees → generate invoices for the current month → count reported.
14. As **parent** → Fees → Pay Now → success → status Paid → download the PDF receipt.
15. As **admin** → Fees → collected total has increased by that amount.
16. As **admin** → Notices → publish to audience `parents` → parent sees it, student does not.

---

## 14. Design tokens

Shared by web and mobile (`web/src/theme.ts` and `mobile/src/theme.ts` hold the same values).
Direction: colourful and friendly, matching the reference dashboard mock.

```
primary        #5B4BE0   indigo — sidebar, primary buttons, active nav
primary-dark   #3E2FB5
primary-soft   #EEEBFC   tinted backgrounds, active nav pill
ground         #F6F7FB   app background
surface        #FFFFFF   cards
ink            #1B2333   primary text
ink-soft       #5A6478   secondary text
ink-faint      #8A93A6   labels, meta
rule           #E4E7EF   borders

success        #16A34A   present, paid
warning        #F59E0B   leave, pending
danger         #EF4444   absent, overdue
info           #3B82F6

radius         12px cards · 8px inputs · 999px pills
shadow         0 1px 2px rgba(27,35,51,.05), 0 8px 24px -12px rgba(27,35,51,.18)
spacing scale  4 8 12 16 24 32 48
font           Inter (web) / system (mobile), tabular-nums wherever digits align
```

Semantic colour is reserved for state (present/absent/paid/overdue) and never used
decoratively — a reviewer must be able to read status by colour alone at a glance.

Charts: donuts with a centred figure, bars with a faint grid, no 3D, no gradients.

---

## 15. Seed data specification (`backend/seed.py`)

Idempotent: truncate all tables (respecting FK order) and rebuild. `make seed` must be safe
to run immediately before a live demo.

**School:** Sunrise Public School, Vikas Nagar, Lucknow · academic year 2025-26 ·
primary colour `#5B4BE0`.

| Entity | Count | Shape |
|---|---|---|
| Class sections | 3 | 8-A, 9-A, 10-A |
| Subjects | 6 | English, Hindi, Mathematics, Science, Social Science, Computer |
| Teachers | 6 | `TCH001`–`TCH006`; each class-teaches one section; subjects distributed across sections. **`TCH001` must class-teach 10-A and teach Mathematics to 10-A** — the §13 walkthrough depends on this |
| Students | 24 | 8 per section; roll numbers 1–8 per section. **Admission numbers are assigned 10-A first**: `SPS2024001`–`008` → 10-A, `009`–`016` → 9-A, `017`–`024` → 8-A. This is required so the demo student account `SPS2024001` is in 10-A, the section used throughout the §13 walkthrough |
| Parents | 22 | mobile numbers `9876500001`–`9876500022`. **20 parents have one child; 2 parents have two children each** (20 × 1 + 2 × 2 = 24 students). Those two are `9876500001` and `9876500002`, whose children are siblings within the same section |
| Timetable | 3 × 6 days × 6 periods | 08:00–14:00, realistic subject spread, rooms |
| Attendance | last 60 school days (Mon–Sat) | ~92 % present, ~5 % absent, ~3 % leave, varied per student so percentages differ |
| Exams | 2 | "Term 1 — Unit Test 1", "Term 1 — Half Yearly"; all 6 subjects per section; complete marks |
| Homework | 8 | across sections and subjects; mixed submitted/not, some late |
| Fee structures | 3 | class 8 ₹2,200 · class 9 ₹2,500 · class 10 ₹2,800 per month |
| Fee invoices | 3 months × 24 students | mixed paid / pending / overdue; paid ones carry payment rows and receipt numbers |
| Notices | 6 | mixed audiences including one class-scoped |
| Grade bands | 8 | per §7.5 |

Marks must be varied enough that the performance donut has all four buckets populated and
the top-3 list is not a tie.

### Demo credentials

Login ids are printed on both login screens. Passwords are in `PASSWORDS.md`,
which is gitignored. **Superseded in part:** admission numbers are now
`YYYY` + a six-digit counter (§0.21), so the student login is `2024000001`
and `SPS2024001` no longer exists.

| Role | Login id |
|---|---|
| Admin | `admin@sunrisepublic.edu` |
| Teacher | `TCH001` |
| Student | `2024000001` |
| Parent | `9876500001` |

The parent `9876500001` **must be one of the two with two children**, so the switcher is
visible on the default demo account.

---

## 16. Build order

Backend is test-driven: model → failing test → endpoint → pass. Access-scoping tests come
before feature tests, because they are the part that matters if a school ever runs this.

| Step | Deliverable | Done when |
|---|---|---|
| 1 | Scaffold, docker-compose, config, db session, all SQLAlchemy models, first Alembic migration | `make up && make migrate` creates all 21 tables |
| 2 | `seed.py` | `make seed` twice in a row leaves an identical database |
| 3 | Auth: login, refresh, me, change-password | All four demo accounts log in; wrong role tab is rejected |
| 4 | `services/scoping.py` + `tests/test_scoping.py` | Every deny in the §9 matrix returns 403 |
| 5 | Admin CRUD endpoints | Creating a student produces a working student login |
| 6 | Web shell: auth, layout, sidebar, theme, Students + Teachers + Classes screens | Admin can manage people in the browser |
| 7 | Attendance: teacher write, admin/student/parent read | Walkthrough steps 1–4 pass |
| 8 | Homework: create, submit, submissions list | Walkthrough steps 5–8 pass |
| 9 | Exams and marks, report card computation with grade bands | Walkthrough steps 9–12 pass |
| 10 | Notices with audience filtering | Walkthrough step 16 passes |
| 11 | Fees: generate, pay, receipt PDF, collection view | Walkthrough steps 13–15 pass |
| 12 | Admin dashboard aggregates and charts | Every figure traceable to a query; no fabricated trends |
| 13 | Expo app: login, role routing, all three tab sets | Full walkthrough passes on a phone |
| 14 | `make gen-api`, committed `schema.d.ts`, both clients type-check | `npm run typecheck` clean in web and mobile |
| 15 | README, `docs/API.md`, `docs/ER-DIAGRAM.md`, `docs/DEMO-SCRIPT.md` | A stranger runs it from a cold clone |
| 16 | *(after sign-off only)* `docs/CUSTOMISATION.md` | See §20 |

---

## 17. Test plan

`pytest` against `TEST_DATABASE_URL`. Fixtures in `conftest.py`: a fresh schema per session,
a seeded dataset, and a token fixture per role.

### Scoping tests — write these first (`tests/test_scoping.py`)

| Test | Expect |
|---|---|
| Student B requests student A's results | 403 |
| Student requests another class's homework | 403 |
| Student submits homework not assigned to their section | 403 |
| Parent requests a child not in `parent_student` | 403 |
| Parent attempts to submit homework | 403/405 |
| Teacher marks attendance for a section they do not teach | 403 |
| Teacher enters marks for a paper outside their subject | 403 |
| Teacher publishes a notice to a section they do not teach | 403 |
| Teacher publishes a notice with audience `all` / `students` / `parents` / `teachers` | 403 |
| Admin attempts to log in through a mobile role tab, or a student through the web | 401 |
| Student or parent calls any `/admin/*` route | 403 |
| Any request with no token | 401 |
| Correct credentials through the wrong role tab | 401 |

### Domain tests

Attendance: duplicate `(student, date)` upserts rather than duplicating · future date
rejected · percentage arithmetic.
Homework: `due_date < assigned_date` rejected · empty answer rejected · resubmission
updates · late flag correctness · pending count = roster − submissions.
Marks: `marks > max_marks` rejected · grade band boundaries (91, 81, …, 33, 0) ·
report card excludes absent subjects from totals.
Fees: invoice generation idempotent · paying twice → 409 · receipt number uniqueness ·
`pending` past `due_date` presents as `overdue` · collection total equals the sum of payments.
Notices: each audience value reaches exactly the intended roles.
Stats: every dashboard figure matches an independently computed query.

---

## 18. Explicitly out of scope for v0

Do not build, stub, or add to any menu: push notifications · in-app messaging or chat ·
transport / bus tracking · library · hostel · ID card generation · exam paper generation ·
bulk CSV import · report export (Excel/PDF beyond the fee receipt) · AI features of any kind ·
file or photo uploads · leave applications · PTM booking · multi-tenancy · dark mode ·
multi-language · online payment gateway integration.

The reference dashboard mock contains an "AI Assistant" panel and Transport / Messages /
Reports / Calendar sidebar entries. **These are visual-style reference only.** They are not
part of v0 and must not appear as dead links — an empty screen behind a menu item reads
worse to a reviewer than a shorter menu.

---

## 19. Open items

Record anything decided during implementation that this document did not specify.

| # | Question | Decision | Date |
|---|---|---|---|
| 1 | Postgres 16 is the target, but the build machine had no Docker. How are the tests run? | `make_engine` accepts any SQLAlchemy URL, so the suite also runs on SQLite (`TEST_DATABASE_URL=sqlite:///./test.db`). Postgres remains the production target and the `.env.example` default. `id` columns are `BigInteger().with_variant(Integer, "sqlite")` because SQLite only autoincrements `INTEGER`. | 2026-09-01 |
| 2 | Native Postgres enum types, or VARCHAR + constraint? | VARCHAR-backed (`native_enum=False`) via `models/base.enum_col`. Identical constraint semantics on both backends, and enum value changes do not need an `ALTER TYPE` migration. Enum *values* are exactly as specified in §7.1. | 2026-09-01 |
| 3 | §15 says six teachers each class-teach one section, but there are only three sections. | `TCH001`→10-A, `TCH002`→9-A, `TCH003`→8-A are class teachers; `TCH004`–`TCH006` are subject teachers only. | 2026-09-01 |
| 4 | How are the 18 `class_subject_teacher` rows distributed? | Each section is covered by **three** of the six teachers, two subjects each (groups `[TCH002,TCH001,TCH003]` for 10-A, `[TCH003,TCH004,TCH005]` for 9-A, `[TCH005,TCH006,TCH001]` for 8-A). A rotation across all six would put every teacher inside every section, which would make teacher scoping untestable and the §17 negative tests vacuous. `TCH001` still teaches Mathematics to 10-A as §15 requires. | 2026-09-01 |
| 5 | The seed windows (60 attendance days, 3 fee months) drift with the wall clock. | `seed.TODAY` is pinned to `2026-09-01` so re-seeding is reproducible. Change that constant to move the demo window. | 2026-09-01 |
| 6 | `from`/`to` on `/admin/attendance/summary` are Python keywords. | Kept as the wire names via `Query(alias="from")`; the handler parameters are `date_from` / `date_to`. | 2026-09-01 |
| 7 | §11 needs an Assignments screen and a Settings screen, but §10 lists no routes for them. | Added `GET /admin/assignments`, `GET /admin/assignments/{id}/submissions`, `GET|PATCH /admin/settings`, `GET /admin/grade-bands`. All read-only for admin except the settings PATCH, which is what makes the template re-skinnable. | 2026-09-01 |
| 8 | §12 needs teacher and parent screens with no matching route in §10. | Added `GET /teacher/dashboard`, `/teacher/profile`, `/teacher/subjects`, `/teacher/classes/{id}/students`, `/admin/classes/{id}/students`, `/parent/profile`. | 2026-09-01 |
| 9 | How does the app fetch an authenticated PDF? | `expo-file-system.downloadAsync` with the bearer header, then the OS share sheet (`expo-sharing`). A token in a query string was rejected — it would leak into logs and share targets. | 2026-09-01 |
| 10 | How is "absent from an exam" entered in the marks screen? | An empty marks box sends no entry for that student, so no `marks` row exists and the report card excludes the subject from the total (§8). Entering `0` means a scored zero and is different. | 2026-09-01 |
| 11 | Recharts renders nothing under React 18 StrictMode with the default entry animation. | `isAnimationActive={false}` on every `Pie` and `Bar`. Charts are read at a glance in a demo; the animation was not worth the failure mode. | 2026-09-01 |
| 12 | `make gen-api` requires the dev server to be up. | Also committed `packages/api-types/openapi.json`, dumped from `app.openapi()`, so the types can be regenerated offline. | 2026-09-01 |
| 13 | Was the suite ever verified against PostgreSQL, or only SQLite? | **Verified on PostgreSQL 18.6** (native install, no Docker), 2026-09-01: `sunrise` and `sunrise_test` both created, migration applied, seed run, `68 passed`. The same suite errored on 66 of 68 tests before Postgres existed, which confirms it connects to Postgres rather than silently falling back to SQLite. `make testdb` uses `docker compose exec` and always fails on a native install — harmless, guarded by `\|\| true`, but create `sunrise_test` by hand. | 2026-09-01 |
| 14 | The project pinned Expo SDK 51; the reviewer's Expo Go is SDK 54 and refuses to open an SDK 51 project. | **Upgraded the project to SDK 54** rather than asking anyone to install an old Expo Go — §3 says "SDK 51+", so 54 is inside the contract, and a demo that requires a downgraded client is not a demo. This pulled React 18.2 → 19.1, React Native 0.74 → 0.81, expo-router 3 → 6, TypeScript 5.3 → 5.9, aligned by `npx expo install --fix`. `npm install` needs `--legacy-peer-deps` on this tree. §3's "51+" is unchanged and still accurate. | 2026-09-02 |
| 15 | SDK 54 removes `downloadAsync` and `cacheDirectory` from the `expo-file-system` root export, breaking the receipt download in #9. | Import from `expo-file-system/legacy`, which is the entry point SDK 54 keeps for exactly this and is the only one that still accepts request headers. The new `File`/`Paths` API has no documented header support, and putting the token in the URL stays rejected for the reason in #9. `cacheDirectory` is now `string \| null`, so the null case is handled with a visible message rather than a `"null…"` path. | 2026-09-02 |
| 16 | `seed.py` wiped `teachers` before `class_sections`, which `class_sections.class_teacher_id` references. | Reordered `WIPE_ORDER` so `ClassSection` is deleted before `Teacher`. **This never failed on SQLite**, which does not enforce foreign keys by default, and never failed on a first run against an empty database — only a *second* `make seed` on populated Postgres, which is exactly the idempotency §16 step 2 requires. Both runs now succeed. | 2026-09-02 |
| 17 | The teacher dashboard listed every period in the teacher's sections, including periods taught by colleagues, showing two 08:00 classes at once. | `stats.today_schedule` takes an optional `teacher_id`; the teacher dashboard passes it. A teacher is scoped to a whole *section* but only takes some of its periods, so filtering by section alone attributes a colleague's class to them. The Timetable tab was already correct, which is what made the inconsistency visible on the device. | 2026-09-02 |
| 18 | Seeded homework titles were paired to subjects by index rotation, filing "Write a Python program to reverse a string" under Social Science. | `HOMEWORK_TITLES` is now `(title, subject_code)` pairs. Not an evidence-integrity breach — the row was real — but the first thing a reviewer notices on the homework screen, and it undermines trust in figures that *are* right. | 2026-09-02 |
| 19 | Tab bars rendered a missing-glyph box on every tab. | No `tabBarIcon` was set, so react-navigation drew a placeholder. Added Ionicons via `@expo/vector-icons`, which already ships with Expo — no new dependency. Icons also stop the 8-tab labels truncating to "Atten…". | 2026-09-02 |
| 20 | §4 claimed both clients import the generated `schema.d.ts`, so a Pydantic rename would break them at compile time. Reading the code on 2026-09-02 showed **neither client imports it** — `web/tsconfig.json` only `include`s the folder, `mobile/tsconfig.json` never mentions it, and both clients hand-write their response types. | §4 corrected to state plainly that this is **not implemented in v0**, with the wiring-up steps recorded there. The claim was left standing through the whole build because the file was generated, committed and type-checked — none of which means it is used. A capability claim in this document is only true if a test or an import proves it; §4 had neither. The types themselves were not wired up in this pass because doing so touches both clients' request paths, which are already demoed and documented. | 2026-09-02 |
| 21 | The deployed admin dashboard took **8.58 s** to load against Vercel's 10 s function timeout. Locally it was instant. | `stats.performance()` and `top_performers()` called `report_card()` once per student and re-queried `grade_bands` each time — an N+1 that localhost hid, because a sub-millisecond round trip to a local Postgres made 100+ queries invisible. Replaced with a single SQL aggregate, `stats.exam_percentages`, and one grade-band load. **8.58 s → 0.93 s.** All 24 students' percentages were compared old-vs-new before shipping: zero mismatches, and the performance buckets and top-3 are byte-identical. The lesson recorded: "works locally" is not "works deployed" — network latency is what turns an N+1 from a style complaint into an outage. | 2026-09-03 |
| 22 | Every table rendered "No students match this filter" **while the request was still in flight**, asserting "none exist" when the truth was "not known yet". | `DataTable` now takes a `loading` prop and shows a loading state instead of the empty state until the first response arrives; applied across all 9 admin screens. This is an evidence-integrity defect, not a cosmetic one: the screen stated a fact it had no basis for. An empty state must mean the query returned nothing, never that the query has not returned. | 2026-09-03 |

---

## 20. After v0 — the customisation guide

**Do not write this until the owner reviews the running system and confirms it is correct.**

Once signed off, produce `docs/CUSTOMISATION.md` covering, for a new school:

1. Branding and identity — `school_settings` row, logo, primary colour, app name and icon.
2. Academic setup — academic year, class sections, subjects, timetable, grade bands.
3. Fee configuration — `fee_structures` per class, billing day, receipt number format.
4. User onboarding — the two paths (admin-created accounts vs. self-signup with a school
   code), what changes in the auth flow to enable the second, and how to bulk-load the
   first intake.
5. What to change in code vs. what is configuration — with an explicit list of every
   hardcoded assumption that would need editing.
6. The multi-tenancy migration path, if one instance ever has to serve several schools:
   add `school_id` to top-level tables, add the predicate to `scoping.py`, extend the token
   claims, and re-run the scoping test suite.
7. Deployment: environment variables, database provisioning, running migrations and the
   seed (or skipping the seed for a real school), and building the Expo app for stores.
