from pathlib import Path

# 1. Update Timetable.tsx
tt_path = Path("web/src/pages/Timetable.tsx")
tt_content = tt_path.read_text(encoding="utf-8")

tt_old_type = "  const [conflicts, setConflicts] = useState<string[]>([]);"
tt_new_type = """  type ConflictItem = string | { kind?: string; detail: string; slot_id?: number };
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);"""

tt_old_map = """              {conflicts.map((c, i) => (
                <li key={i}>{c}</li>
              ))}"""
tt_new_map = """              {conflicts.map((c, i) => (
                <li key={i}>{typeof c === "string" ? c : c.detail}</li>
              ))}"""

tt_old_call = "api.rawPost<{ ok: boolean; conflicts: string[] }>"
tt_new_call = "api.rawPost<{ ok: boolean; conflicts: ConflictItem[] }>"

if tt_old_type in tt_content:
    tt_content = tt_content.replace(tt_old_type, tt_new_type, 1)
if tt_old_map in tt_content:
    tt_content = tt_content.replace(tt_old_map, tt_new_map, 1)
if tt_old_call in tt_content:
    tt_content = tt_content.replace(tt_old_call, tt_new_call, 1)
tt_path.write_text(tt_content, encoding="utf-8")
print("Updated Timetable.tsx")

# 2. Update Classes.tsx
cl_path = Path("web/src/pages/Classes.tsx")
cl_content = cl_path.read_text(encoding="utf-8")

cl_old_type = "  const [conflicts, setConflicts] = useState<string[]>([]);"
cl_new_type = """  type ConflictItem = string | { kind?: string; detail: string; slot_id?: number };
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);"""

cl_old_map = """              {conflicts.map((c, i) => (
                <li key={i}>{c}</li>
              ))}"""
cl_new_map = """              {conflicts.map((c, i) => (
                <li key={i}>{typeof c === "string" ? c : c.detail}</li>
              ))}"""

cl_old_call = "api.rawPost<{ ok: boolean; conflicts: string[] }>"
cl_new_call = "api.rawPost<{ ok: boolean; conflicts: ConflictItem[] }>"

if cl_old_type in cl_content:
    cl_content = cl_content.replace(cl_old_type, cl_new_type, 1)
if cl_old_map in cl_content:
    cl_content = cl_content.replace(cl_old_map, cl_new_map, 1)
if cl_old_call in cl_content:
    cl_content = cl_content.replace(cl_old_call, cl_new_call, 1)
cl_path.write_text(cl_content, encoding="utf-8")
print("Updated Classes.tsx")
