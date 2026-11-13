from pathlib import Path

# 1. Update certificates.py to include dues_override in _build_student_snapshot
svc_path = Path("backend/app/services/certificates.py")
svc_code = svc_path.read_text(encoding="utf-8")
old_line = '"remarks": extra.get("remarks", ""),'
new_line = '"remarks": extra.get("remarks", ""),\n        "dues_override": extra.get("dues_override"),'
if old_line in svc_code and '"dues_override": extra.get("dues_override"),' not in svc_code:
    svc_code = svc_code.replace(old_line, new_line, 1)
    svc_path.write_text(svc_code, encoding="utf-8")
    print("Added dues_override to _build_student_snapshot")

# 2. Update test_certificates.py: replace UserRole.staff with UserRole.teacher
test_path = Path("backend/tests/test_certificates.py")
test_code = test_path.read_text(encoding="utf-8")
if "role=UserRole.staff" in test_code:
    test_code = test_code.replace("role=UserRole.staff", "role=UserRole.teacher")
    test_path.write_text(test_code, encoding="utf-8")
    print("Replaced UserRole.staff with UserRole.teacher in test_certificates.py")
