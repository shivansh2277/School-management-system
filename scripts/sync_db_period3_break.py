import sys
sys.path.insert(0, "backend")

from sqlalchemy import select, update
from app.core.db import SessionLocal
from app.models.academic import SchoolPeriod, TimetableSlot

def sync_periods():
    with SessionLocal() as db:
        # Find period 3 and period 6 for school 1
        p3 = db.scalar(select(SchoolPeriod).where(SchoolPeriod.school_id == 1, SchoolPeriod.period_no == 3))
        p6 = db.scalar(select(SchoolPeriod).where(SchoolPeriod.school_id == 1, SchoolPeriod.period_no == 6))

        if not p3 or not p6:
            print("Error: Could not find Period 3 or Period 6")
            return

        print(f"Before: Period 3 (id={p3.id}, is_break={p3.is_break}), Period 6 (id={p6.id}, is_break={p6.is_break})")
        
        # Move slots from period 3 to period 6
        slots_on_p3 = db.scalars(select(TimetableSlot).where(TimetableSlot.period_id == p3.id)).all()
        print(f"Moving {len(slots_on_p3)} slots from Period 3 to Period 6...")
        for s in slots_on_p3:
            s.period_id = p6.id

        # Update period definitions
        p3.is_break = True
        p3.name = "Break"
        
        p6.is_break = False
        p6.name = None

        db.commit()
        print("Committed period updates to database.")

        # Verify
        p3_new = db.scalar(select(SchoolPeriod).where(SchoolPeriod.id == p3.id))
        p6_new = db.scalar(select(SchoolPeriod).where(SchoolPeriod.id == p6.id))
        p3_slots = db.query(TimetableSlot).filter(TimetableSlot.period_id == p3.id).count()
        p6_slots = db.query(TimetableSlot).filter(TimetableSlot.period_id == p6.id).count()

        print(f"After: Period 3 is_break={p3_new.is_break}, name={p3_new.name}, slots={p3_slots}")
        print(f"After: Period 6 is_break={p6_new.is_break}, name={p6_new.name}, slots={p6_slots}")

if __name__ == "__main__":
    sync_periods()
