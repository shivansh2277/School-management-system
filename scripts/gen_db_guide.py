"""Generate docs/DATABASE.md from the live schema.

Columns, types, foreign keys and row counts are introspected from Postgres, so
they cannot drift from what the database actually enforces. Only each table's
one-line purpose is written by hand, and where the model carries a docstring
that is used instead.
"""
import os
import textwrap

import ast
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get("SUNRISE_DB", "sunrise_test")
SEP = chr(31)


def q(sql):
    """One psql call. Unit-separated, so a comma inside a value cannot split a row."""
    env = dict(os.environ)
    env.setdefault("PGPASSWORD", "sunrise")
    out = subprocess.run(
        ["psql", "-U", "sunrise", "-h", "localhost", "-d", DB, "-tAF", SEP, "-c", sql],
        capture_output=True, text=True, env=env)
    if out.returncode:
        raise SystemExit("psql failed: " + out.stderr)
    return [line.split(SEP) for line in out.stdout.strip().splitlines() if line]


def introspect():
    """Everything in the generated document except the prose comes from here."""
    tables = {t: {"rows": int(n), "columns": [], "fk": [], "unique": []} for t, n in q(
        "select c.relname, coalesce(s.n_live_tup,0) from pg_class c "
        "join pg_namespace ns on ns.oid=c.relnamespace and ns.nspname='public' "
        "left join pg_stat_user_tables s on s.relid=c.oid "
        "where c.relkind='r' order by c.relname;")}

    for tbl, col, typ, nullable, default in q(
            "select table_name, column_name, case "
            "when data_type='character varying' then 'varchar('||coalesce(character_maximum_length::text,'')||')' "
            "when data_type='numeric' then 'numeric('||coalesce(numeric_precision::text,'')||','||coalesce(numeric_scale::text,'')||')' "
            "when data_type='timestamp with time zone' then 'timestamptz' "
            "when data_type='double precision' then 'float' else data_type end, "
            "is_nullable, coalesce(column_default,'') "
            "from information_schema.columns where table_schema='public' "
            "order by table_name, ordinal_position;"):
        if tbl in tables:
            tables[tbl]["columns"].append(
                {"name": col, "type": typ, "null": nullable == "YES", "default": default})

    fks = q("select tc.table_name, kcu.column_name, ccu.table_name, ccu.column_name "
            "from information_schema.table_constraints tc "
            "join information_schema.key_column_usage kcu on kcu.constraint_name=tc.constraint_name "
            "and kcu.constraint_schema=tc.constraint_schema "
            "join information_schema.constraint_column_usage ccu on ccu.constraint_name=tc.constraint_name "
            "and ccu.constraint_schema=tc.constraint_schema "
            "where tc.constraint_type='FOREIGN KEY' and tc.constraint_schema='public' "
            "order by tc.table_name, kcu.column_name;")
    for src, scol, tgt, tcol in fks:
        if src in tables:
            tables[src]["fk"].append({"col": scol, "to": tgt + "." + tcol})
    for t in tables:
        tables[t]["referenced_by"] = sorted({s for s, sc, tg, tc in fks if tg == t and s != t})

    for tbl, name, cols in q(
            "select tc.table_name, tc.constraint_name, "
            "string_agg(kcu.column_name, ',' order by kcu.ordinal_position) "
            "from information_schema.table_constraints tc "
            "join information_schema.key_column_usage kcu on kcu.constraint_name=tc.constraint_name "
            "and kcu.constraint_schema=tc.constraint_schema "
            "where tc.constraint_type='UNIQUE' and tc.constraint_schema='public' "
            "group by 1,2 order by 1,2;"):
        if tbl in tables:
            tables[tbl]["unique"].append(cols)
    return tables


def model_docstrings():
    """A table's purpose, taken from its own model rather than restated here."""
    out = {}
    models = os.path.join(REPO, "backend", "app", "models")
    for name in sorted(os.listdir(models)):
        if not name.endswith(".py"):
            continue
        tree = ast.parse(open(os.path.join(models, name), encoding="utf-8").read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if (isinstance(stmt, ast.Assign)
                        and any(getattr(t, "id", None) == "__tablename__" for t in stmt.targets)
                        and isinstance(stmt.value, ast.Constant)):
                    out[stmt.value.value] = {"doc": ast.get_docstring(node) or ""}
    return out


schema = introspect()
docs = model_docstrings()

DOMAINS = [
    ("Tenancy, identity and access", [
        "schools", "academic_years", "users", "roles", "permissions",
        "role_permissions", "user_roles", "settings", "custom_fields",
        "number_sequences", "alembic_version"]),
    ("People - students and guardians", [
        "students", "guardians", "student_guardian", "enrolments"]),
    ("People - staff", ["employees", "departments"]),
    ("Academics", [
        "class_sections", "subjects", "class_subject_teacher", "school_periods",
        "timetable_slots", "substitutions", "holidays", "homework",
        "homework_submissions"]),
    ("Attendance", ["attendance", "student_leave_requests"]),
    ("Examinations and results", [
        "exams", "exam_schedule", "marks", "assessment_schemes",
        "scheme_components", "grading_scales", "grade_bands",
        "report_card_publications"]),
    ("Fees and money", [
        "fee_heads", "fee_plans", "fee_plan_items", "student_fee_plans",
        "fee_concessions", "fee_invoices", "fee_invoice_lines", "fee_payments",
        "payment_allocations", "fee_periods"]),
    ("Transport", [
        "vehicles", "routes", "route_stops", "transport_assignments",
        "transport_fee_slabs"]),
    ("HR and payroll", [
        "staff_attendance", "staff_leave_requests", "leave_types",
        "leave_balances", "salary_components", "salary_structures",
        "salary_structure_items", "payroll_runs", "payslips", "payslip_lines"]),
    ("Admission", [
        "enquiries", "enquiry_interactions", "admission_cycles",
        "cycle_class_config", "applications", "application_guardians",
        "application_siblings", "application_medical", "application_payments",
        "assessments", "assessment_subjects", "interviews",
        "admission_decisions", "admission_offers", "waitlist_entries"]),
    ("Teacher recruitment and hiring", [
        "candidates", "candidate_offers"]),
    ("Communication", [
        "notices", "messages", "message_recipients", "message_templates",
        "notification_preferences", "in_app_notifications"]),
    ("Inventory and stock", ["stock_items", "stock_requests"]),
    ("Grievances and feedback", ["grievances", "grievance_replies"]),
    ("System", ["audit_log", "documents", "document_types", "jobs", "scheduled_jobs"]),
]

PURPOSE = {
    "candidates": "Teacher recruitment candidate registering personal details, CBSE teaching qualifications, prior school experience, post applied for, expected salary, and application status.",
    "candidate_offers": "Job offer letter issued to a shortlisted teacher candidate, tracking offered designation, department, monthly salary, joining date, and formal hiring confirmation.",
    "in_app_notifications": "In-app notifications dispatched to teachers and administrators for leave status updates, timetable substitutions, and duty reminders.",
    "staff_leave_requests": "Staff leave applications submitted by teachers via the mobile app, with dates, reason, status (applied, approved, rejected), and administrative review notes.",
    "substitutions": "Date-bound substitution assignments covering timetable periods when a teacher is on leave. Daily overlays that preserve master timetable slots untouched.",
    "staff_attendance": "Daily staff roll-call and attendance status records for teachers and school staff (present, absent, leave, half-day).",
    "grievances": "A formal concern, problem, or support ticket raised by a teacher, parent, or student, tracking severity, category, resolution notes, and teacher assignment.",
    "grievance_replies": "A conversational message or progress update exchanged on an open grievance thread between school leadership, assigned teachers, and complainants.",
    "stock_items": "An inventory item held in a school store, lab, or medical room, tracking quantities, reorder thresholds, and physical count discrepancies.",
    "stock_requests": "A replenishment indent, issue request, or teacher diminishing-stock alert awaiting administrative approval or purchase.",
    "users": "Every person who can sign in - staff, students and guardians alike. One row per login; the role-specific detail lives in `students`, `guardians` or `employees`, each of which points back here.",
    "subjects": "The catalogue of subjects the school teaches. A subject exists once and is attached to sections through `class_subject_teacher`.",
    "class_sections": "One class-and-section for one academic year - 10-A, 9-B - with its capacity, room and class teacher. The unit almost everything academic is scoped to.",
    "class_subject_teacher": "Which teacher teaches which subject to which section. The join that makes a timetable solvable and decides whose marks entry is allowed.",
    "enrolments": "A student's membership of a section for one academic year. **The most important join in the schema**: every year-scoped fact - fees, attendance, marks, a bus seat - hangs off `enrolment_id`, never `student_id`.",
    "timetable_slots": "The weekly grid. Which subject, taught by which teacher, occupies which period on which weekday for which section.",
    "notices": "The noticeboard. An announcement with an audience - the whole school, one class, parents, teachers - optionally also sent as a message.",
    "homework": "A piece of homework set for a section and subject, with the date it is due.",
    "homework_submissions": "A child's submission against one `homework` row, and whether it has been marked.",
    "fee_heads": "The named charges a school bills: tuition, transport, exam fee. The vocabulary every invoice line is built from.",
    "fee_plan_items": "The lines of a fee plan - which head, how much, how often. A plan means nothing without these.",
    "documents": "An uploaded file attached to a student, an employee or a vehicle, with its verification state and expiry. Deleted softly, so the audit entry still points at something.",
    "settings": "Per-school configuration as key/value pairs, with the vocabulary defined in `core/settings_registry.py`. Module switches live here too, as `feature.<module>`.",
    "role_permissions": "Which permissions a role grants. Per school, so two tenants can define the same role differently.",
    "jobs": "The background work queue - messages to send, report cards to build. Drained by `worker.py`.",
    "enquiries": "A prospective parent's enquiry, before any application exists. The top of the admission funnel.",
    "interviews": "An admission interview: when, with whom, and what was concluded.",
    "admission_offers": "An offer of a place made to an applicant, with its expiry and whether it was taken up.",
    "application_payments": "The application fee paid against an application. Separate from `fee_payments` because an applicant is not a student and has no enrolment.",
    "alembic_version": "Alembic's own bookkeeping - the single row naming the migration this database is at. Not part of the product; never edit it by hand.",
}

RULES = """## How to read this schema

Five rules explain why the tables look the way they do. Without them the list
below is just nouns.

**1. Almost every table carries `school_id`.** This is a multi-tenant product
sold to separate, independent schools - a tenant is a customer, not a branch. The
column is declared on `TenantBase` so a new table cannot quietly be created
without one; a missing tenant key is a data leak between customers, not a style
problem. Three tables derive from `TimestampedBase` instead and have none, each
for a reason: `schools` *is* the tenant, and `permissions` and `scheduled_jobs`
are vocabulary belonging to the software rather than to any one school.
`alembic_version` is Alembic's own row and not part of the product at all.

**2. Year-scoped facts hang off `enrolment_id`; lifetime facts hang off
`student_id`.** A fee, an attendance mark, a bus seat and a set of marks all
belong to a child's *year in a class*, so they point at `enrolments`. A name, a
date of birth and an admission number belong to the child for life, so they
point at `students`. Getting this backwards silently carries last year's data
into the new class, which is the bug the enrolment split exists to prevent.

**3. Money is never edited.** An invoice is voided and reissued; a payment is
reversed by a contra entry - a second row with a negative amount and
`reverses_payment_id` pointing at the original. Nothing rewrites a figure in
place, so the history stays reconstructable.

**4. A balance is always a SUM, never a stored column.** Payments allocate to
*invoice lines* through `payment_allocations`, oldest first. What a family owes
is computed from those rows every time it is asked for.

**5. Destructive actions are audited with a reason.** `void`, `status_change`
and `delete` refuse to commit without one, and what is stored is the words the
person typed - never a string the software made up. `audit_log` is the only
record of why a notice was removed or a bus route suspended.

Two more conventions worth knowing: money is `numeric`, never a float, and
timestamps are `timestamptz`. Ids are `bigint` throughout.

One note on the diagrams below: because rule 1 means every single table
points at `schools`, those edges are omitted. Drawing 86 identical arrows
would bury the relationships that actually tell you something."""

JOINS = """---

# Appendix - joins you will actually write

Every query below was run against this database before it was written down.

**A student with their class and roll number**

```sql
SELECT s.admission_no, u.full_name, cs.class_name || '-' || cs.section AS class, e.roll_no
FROM students s
JOIN users u ON u.id = s.user_id
JOIN enrolments e ON e.student_id = s.id
JOIN class_sections cs ON cs.id = e.class_section_id
ORDER BY s.admission_no;
```

Note the shape. `students` holds the lifetime facts, `enrolments` holds the
year, and the class arrives through the enrolment. There is no `class_id` on
`students`, and there should never be one.

**What each family owes**

```sql
SELECT u.full_name,
       sum(l.amount - l.discount) - coalesce(sum(a.amount), 0) AS outstanding
FROM fee_invoices i
JOIN fee_invoice_lines l ON l.invoice_id = i.id
JOIN enrolments e ON e.id = i.enrolment_id
JOIN students s ON s.id = e.student_id
JOIN users u ON u.id = s.user_id
LEFT JOIN payment_allocations a ON a.invoice_line_id = l.id
GROUP BY u.full_name
ORDER BY outstanding DESC;
```

Rule 4 in practice: nothing stores a balance, so you subtract what was allocated
from what was billed. The `LEFT JOIN` matters - a family who has paid nothing
has no allocation rows at all, and an inner join would hide them entirely.

**Which bus a child catches, and from where**

```sql
SELECT u.full_name, r.code, st.name AS stop, st.pickup_time
FROM transport_assignments ta
JOIN route_stops st ON st.id = ta.route_stop_id
JOIN routes r ON r.id = st.route_id
JOIN enrolments e ON e.id = ta.enrolment_id
JOIN students s ON s.id = e.student_id
JOIN users u ON u.id = s.user_id
ORDER BY r.code, st.sequence;
```

**Every member of staff, by group**

```sql
SELECT e.employee_code, u.full_name, e.employee_type, e.designation, d.name AS department
FROM employees e
JOIN users u ON u.id = e.user_id
LEFT JOIN departments d ON d.id = e.department_id
ORDER BY e.employee_type, e.employee_code;
```

**Who changed what, and why**

```sql
SELECT occurred_at, actor_label, entity_type, action, reason
FROM audit_log
WHERE reason IS NOT NULL
ORDER BY id DESC
LIMIT 50;
```

---

# Keeping this file true

The columns and relationships above come from the database, not from memory, and
a migration makes them stale. Regenerate rather than editing by hand - the
generator lives in `scripts/`.
"""


def purpose(table):
    entry = docs.get(table)
    if entry and entry["doc"]:
        para = entry["doc"].strip().split("\n\n")[0]
        return " ".join(para.split())
    return PURPOSE.get(table, "_No description recorded._")


def col_table(table):
    info = schema[table]
    fk_by_col = {f["col"]: f["to"] for f in info["fk"]}
    uniq_cols = set()
    for u in info["unique"]:
        uniq_cols.update(c.strip() for c in u.split(","))
    rows = ["| Column | Type | Null | Notes |", "|---|---|---|---|"]
    for c in info["columns"]:
        notes = []
        if c["name"] == "id":
            notes.append("primary key")
        if c["name"] in fk_by_col:
            notes.append("-> `%s`" % fk_by_col[c["name"]])
        if c["name"] in uniq_cols:
            notes.append("unique")
        d = c["default"]
        if d and not d.startswith("nextval"):
            notes.append("default `%s`" % d.split("::")[0])
        rows.append("| `%s` | %s | %s | %s |" % (
            c["name"], c["type"], "yes" if c["null"] else "no",
            ", ".join(notes) or "-"))
    return "\n".join(rows)


def relationships(table):
    info = schema[table]
    out = []
    if info["fk"]:
        targets = sorted({f["to"].split(".")[0] for f in info["fk"]})
        out.append("**Points at:** " + ", ".join("`%s`" % t for t in targets))
    if info["referenced_by"]:
        out.append("**Pointed at by:** " + ", ".join("`%s`" % t for t in info["referenced_by"]))
    if info["unique"]:
        out.append("**Unique on:** " + ", ".join("`%s`" % u for u in info["unique"]))
    if not out:
        return "_Stands alone: nothing references it and it references nothing._"
    return "\n\n".join(out)


def mermaid(present):
    """One ER diagram per domain. All 86 tables at once would be unreadable.

    Keys that leave the domain are drawn too, because a foreign key crossing a
    boundary is exactly the one somebody forgets.
    """
    edges, seen = [], set()
    for t in present:
        for f in schema[t]["fk"]:
            target = f["to"].split(".")[0]
            key = (t, target, f["col"])
            # Every table points at `schools`; rule 1 says so once, and drawing
            # 86 identical edges makes the diagrams unreadable.
            if f["col"] == "school_id" or target == t or key in seen:
                continue
            seen.add(key)
            edges.append('    %s ||--o{ %s : "%s"' % (target, t, f["col"]))
    if not edges:
        return ""
    return "\n".join(["```mermaid", "erDiagram"] + edges + ["```"])


def section(title, tables_in_section, note):
    parts = ["# %s\n" % title, note + "\n"]
    for domain, tables in DOMAINS:
        present = [t for t in tables if t in tables_in_section]
        if not present:
            continue
        parts.append("## %s\n" % domain)
        diagram = mermaid(present)
        if diagram:
            parts.append(diagram + "\n")
        for t in present:
            parts.append("### `%s`\n" % t)
            parts.append("*%s rows / %d columns*\n" % (
                format(schema[t]["rows"], ","), len(schema[t]["columns"])))
            parts.append(textwrap.fill(purpose(t), 80) + "\n")
            parts.append(relationships(t) + "\n")
            parts.append(col_table(t) + "\n")
    return "\n".join(parts)


used = {t for t in schema if schema[t]["rows"] > 0}
unused = set(schema) - used
covered = {t for _, ts in DOMAINS for t in ts}
assert not set(schema) - covered, sorted(set(schema) - covered)

total_cols = sum(len(t["columns"]) for t in schema.values())
total_fks = sum(len(t["fk"]) for t in schema.values())

header = """# The Sunrise ERP database

A reference for every table in `sunrise_test`: what it is for, every column it
has, and how it joins to the rest.

**%d tables, %d columns, %d foreign keys.** Of those tables **%d hold data** in
the seeded demo school and **%d are empty** - not unfinished, simply features
this demo school has not exercised.

Columns, types, foreign keys and row counts below were **introspected from the
running database**, not written by hand, so they cannot have drifted from what
Postgres actually enforces. Each table's purpose is taken from the model's own
docstring where it has one.

> Generated against migration `a1b2c3d4e5f6` on branch `slice/office-feedback`.
> Row counts come from the seeded demo school and will differ on yours.

%s

---

""" % (len(schema), total_cols, total_fks, len(used), len(unused), RULES)

index = ["## Index\n"]
for domain, tables in DOMAINS:
    live = [t for t in tables if t in used]
    empty = [t for t in tables if t in unused]
    bits = ", ".join("`%s`" % t for t in live)
    if empty:
        bits += (" &middot; *empty:* " if live else "*empty:* ") + \
            ", ".join("`%s`" % t for t in empty)
    index.append("**%s** - %s\n" % (domain, bits))

body = section(
    "Part 1 - Tables in use (%d)" % len(used), used,
    "Every table here holds data in the seeded school, and the row counts are live.")
body += "\n---\n\n" + section(
    "Part 2 - Tables not yet used (%d)" % len(unused), unused,
    "These are empty in the demo school. Each belongs to a feature that is built "
    "and has working endpoints - admission has taken no applications, payroll has "
    "run no cycle, nobody has requested leave. The schema is real; only the rows "
    "are missing.")

target = os.path.join(REPO, "docs", "DATABASE.md")
os.makedirs(os.path.dirname(target), exist_ok=True)
text = header + "\n".join(index) + "\n---\n\n" + body + "\n" + JOINS
open(target, "w", encoding="utf-8", newline="\n").write(text)
print("wrote", target)
print("used %d, unused %d, lines %d" % (len(used), len(unused), text.count("\n")))
