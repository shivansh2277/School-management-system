import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.models.academic import ClassSection
from app.models.enums import AttendanceStatus
from app.models.ops import Attendance, Holiday
from app.models.enrolment import Enrolment
from app.models.tenancy import School
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session, sessionmaker

def get_last_n_working_days(db: Session, school_id: int, anchor: date, count: int = 10) -> list[date]:
    """Calculate the count most recent working days on or before anchor date.
    
    Excludes Sundays (weekday == 6) and declared school holidays from the holidays table.
    """
    # Fetch school holidays
    holidays = db.query(Holiday).filter(
        Holiday.school_id == school_id,
        Holiday.status == "active"
    ).all()
    holiday_dates = set()
    for h in holidays:
        # holiday spans from start_date to end_date (or single date)
        s = h.start_date or h.date
        e = h.end_date or h.date or s
        cur = s
        while cur <= e:
            holiday_dates.add(cur)
            cur += timedelta(days=1)

    working = []
    cursor = anchor
    while len(working) < count:
        # Skip Sundays (weekday 6) and holidays
        if cursor.weekday() != 6 and cursor not in holiday_dates:
            working.append(cursor)
        cursor -= timedelta(days=1)
    
    return sorted(working)

def run_retention_and_seed(db: Session, school_id: int, anchor: date, working_days_count: int, dry_run: bool):
    print("=" * 70)
    print("SUNRISE SCHOOL ERP - ATTENDANCE RETENTION & DEMO SEED")
    print(f"School ID: {school_id}")
    print(f"Anchor Date: {anchor}")
    print(f"Retained Working Days: {working_days_count}")
    print(f"Mode: {'DRY-RUN (NO CHANGES APPLIED)' if dry_run else 'APPLY (DATABASE WILL BE UPDATED)'}")
    print("=" * 70)

    # 1. Verify tenant exists
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise ValueError(f"School with ID {school_id} not found!")
    print(f"Tenant: {school.name} (Code: {school.code})")

    # 2. Determine target working days
    target_dates = get_last_n_working_days(db, school_id, anchor, count=working_days_count)
    min_target_date = target_dates[0]
    max_target_date = target_dates[-1]
    print(f"\nCalculated {len(target_dates)} working days:")
    for i, d in enumerate(target_dates, 1):
        weekday_name = d.strftime("%A")
        print(f"  Day {i:2d}: {d} ({weekday_name})")

    # 3. Analyze current attendance table
    total_existing = db.query(func.count(Attendance.id)).filter(
        Attendance.school_id == school_id
    ).scalar() or 0

    older_records_count = db.query(func.count(Attendance.id)).filter(
        Attendance.school_id == school_id,
        Attendance.date < min_target_date
    ).scalar() or 0

    within_window_count = db.query(func.count(Attendance.id)).filter(
        Attendance.school_id == school_id,
        Attendance.date >= min_target_date,
        Attendance.date <= max_target_date
    ).scalar() or 0

    future_records_count = db.query(func.count(Attendance.id)).filter(
        Attendance.school_id == school_id,
        Attendance.date > max_target_date
    ).scalar() or 0

    print(f"\nCurrent Attendance in DB for School {school_id}:")
    print(f"  Total records: {total_existing}")
    print(f"  Records older than {min_target_date} (to be deleted): {older_records_count}")
    print(f"  Records within target 10-day window: {within_window_count}")
    if future_records_count > 0:
        print(f"  Records after {max_target_date} (outside window): {future_records_count}")

    # 4. Fetch all active enrolments
    enrolments = db.query(Enrolment).filter(
        Enrolment.school_id == school_id,
        Enrolment.status == "active"
    ).all()
    total_enrolments = len(enrolments)
    print(f"\nActive Enrolled Students: {total_enrolments}")

    # Map sections and class teachers
    sections = db.query(ClassSection).filter(ClassSection.school_id == school_id).all()
    class_teacher_of = {s.id: s.class_teacher_id for s in sections}

    # Deterministic RNG based on seed for reproducible realistic distribution
    rng = random.Random(42)

    # 5. Plan generation / updates
    to_insert = []
    to_update = []
    
    # Check existing attendance in the 10-day window
    existing_window_rows = db.query(Attendance).filter(
        Attendance.school_id == school_id,
        Attendance.date.in_(target_dates)
    ).all()
    existing_map = {(a.enrolment_id, a.date): a for a in existing_window_rows}

    status_distribution = {"present": 0, "absent": 0, "leave": 0}

    for e in enrolments:
        marker = class_teacher_of.get(e.class_section_id, 1)
        roll_seed = e.roll_no or e.id
        absent_rate = 0.02 + (roll_seed % 4) * 0.02  # between 2% and 8%
        leave_rate = 0.03  # 3%

        for d in target_dates:
            roll = rng.random()
            if roll < absent_rate:
                stat = AttendanceStatus.absent
            elif roll < absent_rate + leave_rate:
                stat = AttendanceStatus.leave
            else:
                stat = AttendanceStatus.present

            status_distribution[stat.value] += 1

            existing_record = existing_map.get((e.id, d))
            if existing_record:
                # Record exists; ensure marker and status are consistent
                if existing_record.status != stat:
                    to_update.append((existing_record, stat))
            else:
                to_insert.append(
                    Attendance(
                        school_id=school_id,
                        enrolment_id=e.id,
                        date=d,
                        status=stat,
                        marked_by=marker,
                        remarks="DEMO/SYNTHETIC",
                    )
                )

    total_expected = total_enrolments * len(target_dates)
    print(f"\nTarget Attendance Calculation:")
    print(f"  Enrolled students: {total_enrolments}")
    print(f"  Target working days: {len(target_dates)}")
    print(f"  Total expected records: {total_expected}")
    print(f"  Existing records in window: {len(existing_map)}")
    print(f"  New records to insert: {len(to_insert)}")
    print(f"  Records to update: {len(to_update)}")
    print(f"\nTarget Status Distribution:")
    for st, cnt in status_distribution.items():
        pct = (cnt / total_expected) * 100 if total_expected else 0
        print(f"  {st.capitalize():7s}: {cnt:4d} ({pct:5.1f}%)")

    # 6. Apply if not dry_run
    if not dry_run:
        # A. Delete older records
        if older_records_count > 0:
            deleted_rows = db.query(Attendance).filter(
                Attendance.school_id == school_id,
                Attendance.date < min_target_date
            ).delete(synchronize_session=False)
            print(f"\n[APPLIED] Deleted {deleted_rows} older attendance records (date < {min_target_date}).")

        # B. Insert missing records
        for item in to_insert:
            db.add(item)
        if to_insert:
            print(f"[APPLIED] Inserted {len(to_insert)} new synthetic attendance records.")

        # C. Update differing records if any
        for rec, new_stat in to_update:
            rec.status = new_stat
            rec.remarks = "DEMO/SYNTHETIC"
        if to_update:
            print(f"[APPLIED] Updated {len(to_update)} existing records.")

        db.flush()
        db.commit()
        print("\nDatabase transaction successfully committed!")

        # D. Post-verification
        final_count = db.query(func.count(Attendance.id)).filter(
            Attendance.school_id == school_id
        ).scalar()
        print(f"Final attendance rows in DB: {final_count} (Expected: {total_expected})")
        assert final_count == total_expected, f"Count mismatch! Expected {total_expected}, got {final_count}"
        print("Verification SUCCESSFUL: 100% of students have attendance for all 10 working days.")
    else:
        print("\n[DRY-RUN] No records were deleted, inserted, or updated.")
        print(f"To apply these changes, rerun with --apply.")

def main():
    parser = argparse.ArgumentParser(description="Attendance Retention & Demo Generation")
    parser.add_argument("--school-id", type=int, default=1, help="School ID (tenant)")
    parser.add_argument("--days", type=int, default=10, help="Number of working days to retain/generate")
    parser.add_argument("--anchor", type=str, default="2026-09-01", help="Anchor date YYYY-MM-DD")
    parser.add_argument("--apply", action="store_true", help="Apply changes to DB (destructive deletion + seed)")
    args = parser.parse_args()

    anchor_date = date.fromisoformat(args.anchor)
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        run_retention_and_seed(
            db=session,
            school_id=args.school_id,
            anchor=anchor_date,
            working_days_count=args.days,
            dry_run=not args.apply
        )
    finally:
        session.close()

if __name__ == "__main__":
    main()
