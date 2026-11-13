import os

path = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "core", "permissions.py")
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

dup = '''    (
        "academic_coordinator",
        "Academic Coordinator",
        [
            "academics.class.read",
            "timetable.slot.read",
            "timetable.slot.write",
            "timetable.slot.override",
            "timetable.substitution.manage",
            "comms.notice.read",
        ],
    ),
    (
        "academic_coordinator",
        "Academic Coordinator",
        [
            "academics.class.read",
            "timetable.slot.read",
            "timetable.slot.write",
            "timetable.slot.override",
            "timetable.substitution.manage",
            "comms.notice.read",
        ],
    ),'''

single = '''    (
        "academic_coordinator",
        "Academic Coordinator",
        [
            "academics.class.read",
            "timetable.slot.read",
            "timetable.slot.write",
            "timetable.slot.override",
            "timetable.substitution.manage",
            "comms.notice.read",
        ],
    ),'''

if dup not in text:
    dup = dup.replace("\n", "\r\n")
    single = single.replace("\n", "\r\n")

assert dup in text, "dup not found"
text = text.replace(dup, single, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("Removed duplicate academic_coordinator from permissions.py")
