"""
Export all tables from PostgreSQL sunrise_test into clean CSV files
and generate a dataset package suitable for uploading directly to Kaggle.
"""

import os
import csv
import json
from pathlib import Path
from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg://sunrise:sunrise@localhost:5432/sunrise_test"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "kaggle_dataset"

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_dir = OUT_DIR / "csv_tables"
    csv_dir.mkdir(exist_ok=True)

    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        # Get all public tables
        tables = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        )).scalars().all()

        manifest = []
        total_rows = 0

        for table in tables:
            # Query all rows
            result = conn.execute(text(f'SELECT * FROM "{table}"'))
            columns = list(result.keys())
            rows = result.fetchall()
            
            if not rows:
                continue

            csv_path = csv_dir / f"{table}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in rows:
                    writer.writerow([
                        json.dumps(val) if isinstance(val, (dict, list)) else val
                        for val in row
                    ])

            manifest.append({
                "table": table,
                "rows": len(rows),
                "columns": len(columns),
                "file": f"csv_tables/{table}.csv"
            })
            total_rows += len(rows)
            print(f"Exported {table}: {len(rows)} rows, {len(columns)} cols")

    # Generate Kaggle Dataset README
    readme_content = f"""# Sunrise School ERP — Comprehensive Academic & Operational Dataset

## Overview
This dataset contains real-world structured relational data from the **Sunrise School ERP** system (CBSE Affiliated K-12 School Management System).
It encompasses student lifecycle records, academic grades, examination scores, daily attendance logs, fee billing and transactions, timetable scheduling, staff payroll, recruitment, and inventory catalog.

- **Total Tables**: {len(manifest)} relational tables
- **Total Records**: {total_rows:,} rows
- **Format**: Standard CSV (UTF-8) with headers

## Key Relational Domains & Tables
1. **Students & Demographics**:
   - `students.csv` — Permanent student identity, registration, DOB, blood group, admission numbers.
   - `enrolments.csv` — Academic session enrollments, class & section memberships, promotion status.
   - `guardians.csv` & `student_guardian.csv` — Parents, emergency contacts, occupations.
2. **Academics & Examinations**:
   - `marks.csv` — 2,400 exam score records with subject breakdown and grade scales.
   - `attendance.csv` — 5,800 daily period attendance entries with Present/Absent/Late status.
   - `homework.csv` & `homework_submissions.csv` — Homework assignments, digital turn-in status, marks.
   - `timetable_slots.csv` — Weekly period schedule across classes, teachers, and subjects.
3. **Finance & Fee Management**:
   - `fee_invoices.csv` & `fee_invoice_lines.csv` — Term tuition, transport, admission fee breakdown.
   - `fee_payments.csv` & `payment_allocations.csv` — Cash, bank, and online receipt allocations.
4. **Staff, HR & Payroll**:
   - `employees.csv` — Teacher and staff master directory, departments, qualification.
   - `salary_structures.csv` & `salary_components.csv` — CTC, EPF, ESI, and tax structures.
5. **School Operations**:
   - `stock_items.csv` & `stock_requests.csv` — School inventory, consumption, minimum threshold levels.
   - `grievances.csv` & `grievance_replies.csv` — Parent/Teacher support ticketing and audit logs.
   - `routes.csv` & `route_stops.csv` — Bus fleet transit stops and passenger assignments.

## Primary Invariants & Primary/Foreign Keys
- `students.id` is the permanent student record across all years.
- `enrolments.id` is the session-scoped record (`marks`, `attendance`, and `homework_submissions` link strictly to `enrolment_id`).
- All tables maintain multi-tenant isolation via `school_id`.
"""
    with open(OUT_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"\nSuccessfully generated Kaggle Dataset at: {OUT_DIR}")
    print(f"Total exported tables: {len(manifest)}, Total rows: {total_rows}")

if __name__ == "__main__":
    main()
