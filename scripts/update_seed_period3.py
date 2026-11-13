from pathlib import Path

p = Path("backend/seed.py")
c = p.read_text(encoding="utf-8")

old_text = '            is_break=(i + 1 == 6),\n            name="Break" if i + 1 == 6 else None,'
new_text = '            is_break=(i + 1 == 3),\n            name="Break" if i + 1 == 3 else None,'

if old_text in c:
    c = c.replace(old_text, new_text, 1)
    p.write_text(c, encoding="utf-8")
    print("Updated seed.py (LF)")
elif old_text.replace("\n", "\r\n") in c:
    c = c.replace(old_text.replace("\n", "\r\n"), new_text.replace("\n", "\r\n"), 1)
    p.write_text(c, encoding="utf-8")
    print("Updated seed.py (CRLF)")
else:
    print("Target not found in seed.py")
