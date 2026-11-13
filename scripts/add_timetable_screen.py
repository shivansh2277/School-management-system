from pathlib import Path

p = Path("web/src/screens.ts")
c = p.read_text(encoding="utf-8")

entry_lf = """  {
    path: "/timetable",
    label: "Timetable",
    group: "Academics",
    permissions: ["timetable.slot.read"],
    modules: ["timetable"],
    excludeRoles: ["transport_incharge"],
    element: lazy(() => import("./pages/Timetable").then((m) => ({ default: m.Timetable }))),
  },
"""

classes_lf = '  {\n    path: "/classes",'
classes_crlf = '  {\r\n    path: "/classes",'

if classes_lf in c:
    c = c.replace(classes_lf, entry_lf + classes_lf, 1)
    p.write_text(c, encoding="utf-8")
    print("Success LF")
elif classes_crlf in c:
    c = c.replace(classes_crlf, entry_lf.replace("\n", "\r\n") + classes_crlf, 1)
    p.write_text(c, encoding="utf-8")
    print("Success CRLF")
else:
    print("Could not find classes entry!")
