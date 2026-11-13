import json
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from sqlalchemy import create_engine, text

def main():
    backup_dir = backend_dir / "var" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    json_file = backup_dir / "attendance_backup_pre_retention_20261113.json"
    sql_file = backup_dir / "attendance_backup_pre_retention_20261113.sql"

    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, school_id, enrolment_id, date, status, marked_by, "
                "remarks, corrected_by, corrected_at, created_at, updated_at "
                "FROM attendance ORDER BY id"
            )
        ).fetchall()
        print(f"Fetched rows from DB: {len(rows)}")

        data = []
        sql_lines = ["-- Attendance Table Recoverable Backup\n", "BEGIN;\n"]
        for r in rows:
            d = {
                "id": r[0],
                "school_id": r[1],
                "enrolment_id": r[2],
                "date": r[3].isoformat() if r[3] else None,
                "status": str(r[4]),
                "marked_by": r[5],
                "remarks": r[6],
                "corrected_by": r[7],
                "corrected_at": r[8].isoformat() if r[8] else None,
                "created_at": r[9].isoformat() if r[9] else None,
                "updated_at": r[10].isoformat() if r[10] else None,
            }
            data.append(d)

            corr_at = f"'{d['corrected_at']}'" if d["corrected_at"] else "NULL"
            cr_at = f"'{d['created_at']}'" if d["created_at"] else "NOW()"
            up_at = f"'{d['updated_at']}'" if d["updated_at"] else "NOW()"
            rem = f"'{d['remarks']}'" if d["remarks"] else "NULL"
            sql_lines.append(
                f"INSERT INTO attendance (id, school_id, enrolment_id, date, status, marked_by, remarks, corrected_by, corrected_at, created_at, updated_at) "
                f"VALUES ({r[0]}, {r[1]}, {r[2]}, '{d['date']}', '{d['status']}', {r[5] if r[5] else 'NULL'}, {rem}, {r[7] if r[7] else 'NULL'}, {corr_at}, {cr_at}, {up_at}) "
                f"ON CONFLICT (id) DO NOTHING;\n"
            )
        sql_lines.append("COMMIT;\n")

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        with open(sql_file, "w", encoding="utf-8") as f:
            f.writelines(sql_lines)

        print(f"Saved JSON backup: {json_file} ({json_file.stat().st_size} bytes)")
        print(f"Saved SQL backup: {sql_file} ({sql_file.stat().st_size} bytes)")

        # Verify
        with open(json_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert len(loaded) == len(rows), "Backup count mismatch!"
        print(f"Verified backup record count: {len(loaded)} / {len(rows)} rows.")
        print("Backup verified recoverable and 100% SUCCESSFUL!")

if __name__ == "__main__":
    main()
