import os

def update_ssot():
    path = "school-management-system/SINGLE_SOURCE_OF_TRUTH.md"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    target = """5. **Bell Timings / School Periods**:
   - Master list of school periods, start/end times, durations, and lesson vs break types.
   - `+ Add School Period` modal supporting instructional lessons, recess, lunch breaks, and assemblies.

### 14.3 Full Audit Logging
All timetable actions are comprehensively recorded in `audit_logs`:
- School period creation (`entity_type="school_period"`, `action=create`)."""

    replacement = """5. **Bell Timings / School Periods**:
   - Master list of school periods, start/end times, durations, and lesson vs break types.
   - Period 3 defaults to the school-wide Break/Recess (10:00 - 10:20), dynamically configurable without hardcoding.
   - 1-click "Set as Break" / "Set as Lesson" toggling and "Edit / Configure" modal (`PUT /admin/timetable/periods/{id}`).
   - Safe period deletion (`DELETE /admin/timetable/periods/{id}`) with integrity checks preventing deletion of periods with active slots.
   - `+ Add School Period` modal supporting instructional lessons, recess, lunch breaks, and assemblies.

### 14.3 Full Audit Logging
All timetable actions are comprehensively recorded in `audit_logs`:
- School period creation (`entity_type="school_period"`, `action=create`).
- School period updates and break toggling (`entity_type="school_period"`, `action=update`).
- School period deletion (`entity_type="school_period"`, `action=delete`)."""

    normalized_content = content.replace("\r\n", "\n")
    normalized_target = target.replace("\r\n", "\n")
    normalized_replacement = replacement.replace("\r\n", "\n")

    if normalized_target in normalized_content:
        new_content = normalized_content.replace(normalized_target, normalized_replacement)
        with open(path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(new_content)
        print("Updated SINGLE_SOURCE_OF_TRUTH.md successfully.")
    else:
        print("Target not found in SINGLE_SOURCE_OF_TRUTH.md.")

def update_claude_md():
    path = "school-management-system/CLAUDE.md"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    target = """- **Report Card Academic Result vs Withholding**: Academic evaluation (`pass`, `fail`, `compartment`) is determined strictly by CBSE criteria (33% subject & aggregate threshold). Never hardcode PASS. Fee-related report-card withholding is recorded in `is_withheld` and must never alter the academic grade or result string."""
    
    addition = """- **Report Card Academic Result vs Withholding**: Academic evaluation (`pass`, `fail`, `compartment`) is determined strictly by CBSE criteria (33% subject & aggregate threshold). Never hardcode PASS. Fee-related report-card withholding is recorded in `is_withheld` and must never alter the academic grade or result string.
- **Configurable Timetable Break Periods**: School breaks (recess/lunch) are dynamically driven by `school_periods.is_break` and never hardcoded by index. Period 3 is the configured default recess, with Period 6 as instructional lesson. All timetable conflict detection, teacher load statistics, completeness matrices, and UI slots dynamically reflect periods according to their database `is_break` flag."""

    normalized_content = content.replace("\r\n", "\n")
    normalized_target = target.replace("\r\n", "\n")
    normalized_addition = addition.replace("\r\n", "\n")

    if normalized_target in normalized_content:
        new_content = normalized_content.replace(normalized_target, normalized_addition)
        with open(path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(new_content)
        print("Updated CLAUDE.md successfully.")
    else:
        print("Target not found in CLAUDE.md.")

def update_memory_md():
    path = "school-management-system/MEMORY.md"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    target = """35. **Dynamic CBSE Academic Evaluation Invariant**:
    - Term report card academic status (`card.result`) is evaluated strictly against CBSE criteria (>= 33% subject threshold, >= 33% aggregate threshold, 1 failure = COMPARTMENT, >= 2 failures or aggregate < 33% = FAIL). PASS is never hardcoded. Fee dues withholding is maintained orthogonally via `card.is_withheld` and never alters academic performance metrics."""

    addition = """35. **Dynamic CBSE Academic Evaluation Invariant**:
    - Term report card academic status (`card.result`) is evaluated strictly against CBSE criteria (>= 33% subject threshold, >= 33% aggregate threshold, 1 failure = COMPARTMENT, >= 2 failures or aggregate < 33% = FAIL). PASS is never hardcoded. Fee dues withholding is maintained orthogonally via `card.is_withheld` and never alters academic performance metrics.
36. **Configurable School Period Break Invariant**:
    - School breaks (recess/lunch) must never be hardcoded to a fixed period index in services, calculations, or frontend grids. `SchoolPeriod.is_break` dynamically determines whether a period is instructional or non-instructional. Period 3 defaults to Break/Recess (10:00 - 10:20), with full API (`PUT /admin/timetable/periods/{id}`) and Web UI support for Academic Coordinators and Admins to reconfigure period labels, times, and break statuses at any time."""

    normalized_content = content.replace("\r\n", "\n")
    normalized_target = target.replace("\r\n", "\n")
    normalized_addition = addition.replace("\r\n", "\n")

    if normalized_target in normalized_content:
        new_content = normalized_content.replace(normalized_target, normalized_addition)
        with open(path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(new_content)
        print("Updated MEMORY.md successfully.")
    else:
        print("Target not found in MEMORY.md.")

if __name__ == "__main__":
    update_ssot()
    update_claude_md()
    update_memory_md()
