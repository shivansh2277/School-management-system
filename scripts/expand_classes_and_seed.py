"""Idempotent seed expansion script for Sunrise School ERP.

Expands academic classes by adding 9 academic groups:
Pre-primary:
  - Nursery-A
  - LKG-A
  - UKG-A
Senior Secondary:
  - Class 11 (Science, Commerce, Humanities) -> 11-Sci, 11-Com, 11-Hum
  - Class 12 (Science, Commerce, Humanities) -> 12-Sci, 12-Com, 12-Hum

For every added group:
  - Demo students (10 per section) with enrolments and parent accounts
  - Subjects, class teachers, and subject teachers (CST)
  - Timetable entries balancing teacher workload (30 slots per section, Mon-Sat)
  - Valid fee plans with standard heads (Tuition, Development, Transport)

Also cleans up student attendance:
  - Deletes attendance records dated prior to 1 October 2026
  - Seeds October 1, 2, 3 demo attendance
  - Preserves Sunday 4 October 2026 as non-school/unmarked day
"""

from __future__ import annotations

import os
import sys

# Ensure backend app is on sys.path and load backend/.env
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_path, ".env"))

from app.core.db import SessionLocal
from app.services.seed_expansion import expand_database


if __name__ == "__main__":
    db = SessionLocal()
    try:
        print("Starting idempotent database expansion...")
        results = expand_database(db)
        print("Database expansion complete. Summary of changes:")
        for k, v in results.items():
            print(f"  - {k}: {v}")
    except Exception as e:
        db.rollback()
        print(f"Error during expansion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
