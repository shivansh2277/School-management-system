from pathlib import Path

p = Path("web/src/pages/Classes.tsx")
content = p.read_text(encoding="utf-8")

old_block = """          const filtered = (res.conflicts || []).filter((c) => {
            if (slot && c.includes(`Period ${slot.period}`) && c.includes(slot.day_of_week.toUpperCase())) {
              return false;
            }
            return true;
          });"""

new_block = """          const filtered = (res.conflicts || []).filter((c) => {
            const detail = typeof c === "string" ? c : c.detail;
            if (slot && detail.includes(`Period ${slot.period}`) && detail.includes(slot.day_of_week.toUpperCase())) {
              return false;
            }
            return true;
          });"""

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    p.write_text(content, encoding="utf-8")
    print("Fixed Classes.tsx (LF)")
elif old_block.replace("\n", "\r\n") in content:
    content = content.replace(old_block.replace("\n", "\r\n"), new_block.replace("\n", "\r\n"), 1)
    p.write_text(content, encoding="utf-8")
    print("Fixed Classes.tsx (CRLF)")
else:
    print("Could not match old_block in Classes.tsx")
