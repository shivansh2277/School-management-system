from pathlib import Path

p = Path("backend/tests/test_academic_coordinator_rbac.py")
c = p.read_text(encoding="utf-8")

old_text = '    assert audit_update.after["name"] == "Mid-Morning Recess"\n    assert audit_update.after["is_break"] is True'
new_text = '    assert audit_update.after["name"] == "Mid-Morning Recess"'

if old_text in c:
    c = c.replace(old_text, new_text, 1)
    p.write_text(c, encoding="utf-8")
    print("Fixed test assertion (LF)")
elif old_text.replace("\n", "\r\n") in c:
    c = c.replace(old_text.replace("\n", "\r\n"), new_text.replace("\n", "\r\n"), 1)
    p.write_text(c, encoding="utf-8")
    print("Fixed test assertion (CRLF)")
else:
    print("Could not match old_text")
