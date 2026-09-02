# API

Base URL `/`. Everything except `/auth/login` and `/auth/refresh` requires
`Authorization: Bearer <token>`. The live, always-current reference is
`http://localhost:8000/docs`; this page is the map and the conventions.

## Conventions

- Errors are `{ "detail": "<message>" }`. Codes: `400` invalid request, `401`
  missing/expired token or wrong role tab, `403` out of scope, `404` not found,
  `409` conflict, `422` validation.
- Routes taking `?page` return `{ items, total, page, page_size }` with a default
  `page_size` of 25. Everything else returns a bare array.
- Dates are `YYYY-MM-DD`; timestamps are ISO 8601 with timezone. Money is a
  string-serialised decimal with two places, never a float; the clients add the
  currency symbol.
- Any response naming a person carries both `id` and `full_name`, so no client
  needs a second call to render a row.

## Auth

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/auth/login` | `{role, login_id, password}` | tokens + user |
| POST | `/auth/refresh` | `{refresh_token}` | new access token |
| GET | `/auth/me` | - | user + the role-specific profile block |
| POST | `/auth/change-password` | `{old_password, new_password}` | `204` |

`role` selects which tab the user came from and must equal `users.role`, so
correct credentials sent through the wrong tab are a `401`. That is what keeps an
admin off the mobile app and a student off the web dashboard.

`/auth/me` inlines the role profile so a client needs one call at boot: student
gets `admission_no`, `class_label`, `roll_no`; teacher gets `employee_id` and
`sections`; parent gets `children[]`, which drives the switcher; admin gets nothing
extra.

## Admin

```
GET    /admin/dashboard/stats            every figure is a live query
GET    /admin/settings                   PATCH /admin/settings
GET    /admin/grade-bands

GET    /admin/students?class_section_id&q&page
POST   /admin/students                   creates the student and their parent login in one tx
GET    /admin/students/{id}              PATCH /admin/students/{id}
DELETE /admin/students/{id}              soft delete -> users.is_active = false

GET    /admin/teachers                   POST /admin/teachers
PATCH  /admin/teachers/{id}              DELETE /admin/teachers/{id}

GET    /admin/classes                    POST /admin/classes    PATCH /admin/classes/{id}
GET    /admin/classes/{id}/students
GET    /admin/subjects                   read-only, seeded
GET    /admin/timetable?class_section_id read-only (D8)

GET    /admin/attendance?class_section_id&date      roll for one day, read only
GET    /admin/attendance/summary?from&to&class_section_id

GET    /admin/assignments?class_section_id
GET    /admin/assignments/{id}/submissions

GET    /admin/exams                      POST /admin/exams
POST   /admin/exams/{id}/schedule        GET /admin/exams/{id}/schedule

GET    /admin/notices    POST /admin/notices    DELETE /admin/notices/{id}

GET    /admin/fees/structures
GET    /admin/fees/invoices?month&year&status&class_section_id
POST   /admin/fees/invoices/generate  {month, year}     idempotent
GET    /admin/fees/collection?year
```

`POST /admin/students` accepts either a nested `parent` object (creates a new parent
login) or a `parent_id` (links an existing one). Linking is how siblings are attached
to the same parent account.

`POST /admin/fees/invoices/generate` returns `{created, skipped}`. Running it twice
for the same month creates nothing the second time — the unique key on
`(student_id, month, year)` is what makes that true, not application bookkeeping.

## Teacher

```
GET    /teacher/dashboard
GET    /teacher/classes                  sections and subjects they own
GET    /teacher/classes/{id}/students
GET    /teacher/subjects?class_section_id
GET    /teacher/timetable
GET    /teacher/profile

GET    /teacher/attendance?class_section_id&date        pre-filled if already marked
POST   /teacher/attendance
       { class_section_id, date, entries:[{student_id, status, remarks?}] }

GET    /teacher/homework?class_section_id&subject_id
POST   /teacher/homework   { class_section_id, subject_id, title, description, due_date }
PATCH  /teacher/homework/{id}            DELETE /teacher/homework/{id}
GET    /teacher/homework/{id}/submissions

GET    /teacher/exams                    papers for their (section, subject) pairs
GET    /teacher/marks?exam_schedule_id
POST   /teacher/marks  { exam_schedule_id, entries:[{student_id, marks_obtained}] }

POST   /teacher/announcements  { title, body, class_section_id }
GET    /teacher/announcements
```

`POST /teacher/attendance` is a bulk upsert for one `(class_section, date)`: the
payload carries every student in the section and re-submitting the same date
overwrites. A future date is a `400`.

`POST /teacher/announcements` accepts only `audience = class`, and only for a
section the teacher teaches. Any other audience is a `403` rather than being
silently rewritten, because a `students` notice has no per-section variant and
would broadcast past their scope.

Marks entry rejects anything above the paper's `max_marks` with a `422` naming the
offending student. Omitting a student from the payload leaves them without a marks
row, which the report card reads as absent — excluded from the total, not zero.

## Student

```
GET    /student/dashboard
GET    /student/timetable
GET    /student/profile
GET    /student/notices
GET    /student/attendance?month&year         day-wise plus a monthly summary
GET    /student/homework?status=pending|submitted|all
POST   /student/homework/{id}/submit   { answer_text }
GET    /student/exams
GET    /student/results                       exams they have marks for
GET    /student/results/{exam_id}             full report card
```

Submitting to homework outside their own section is a `403`. An empty answer is a
`422`. Submitting twice updates the row in place and refreshes `submitted_at`; late
submission is allowed and recorded, and the teacher's list flags it.

## Parent

```
GET    /parent/children                       drives the child switcher
GET    /parent/children/{student_id}/summary
GET    /parent/children/{student_id}/attendance?month&year
GET    /parent/children/{student_id}/homework
GET    /parent/children/{student_id}/results
GET    /parent/children/{student_id}/results/{exam_id}
GET    /parent/children/{student_id}/profile
GET    /parent/profile
GET    /parent/notices
GET    /parent/fees?student_id
POST   /parent/fees/{invoice_id}/pay          simulated
GET    /parent/fees/{invoice_id}/receipt.pdf  application/pdf
```

Every `/parent/children/{student_id}/*` route calls `assert_can_read_student` before
anything else; a child not in `parent_student` is a `403`, not an empty result.

Paying an invoice that is already paid is a `409`. The receipt PDF is generated on
demand and requires the bearer header like every other route — the mobile app
downloads it with that header rather than putting a token in a URL.

## Where the rules actually live

Access scoping is in `backend/app/services/scoping.py` and is called from the
service layer, not only from route dependencies, so a new endpoint that forgets a
`require_role` still cannot read another family's child. Every deny in the RBAC
matrix has a negative test in `backend/tests/test_scoping.py`.
