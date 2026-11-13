import os

backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")

# 1. Update permissions.py
perm_path = os.path.join(backend_dir, "app", "core", "permissions.py")
with open(perm_path, "r", encoding="utf-8") as f:
    text = f.read()

target = '    ("super_admin", "Super Admin", SUPER_ADMIN_PERMISSIONS),'
replacement = '''    ("super_admin", "Super Admin", SUPER_ADMIN_PERMISSIONS),
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

if '("academic_coordinator"' not in text:
    assert target in text, "Target not found in permissions.py"
    text = text.replace(target, replacement, 1)
    with open(perm_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("1. permissions.py updated with academic_coordinator.")
else:
    print("1. permissions.py already contains academic_coordinator.")

# 2. Update teachers.py to allow timetable.slot.read for listing teachers
teachers_path = os.path.join(backend_dir, "app", "api", "admin", "teachers.py")
with open(teachers_path, "r", encoding="utf-8") as f:
    t_text = f.read()

t_target = 'admin_only = require_permission("hr.employee.read", school_wide=True)'
t_replacement = 'admin_only = require_permission("hr.employee.read", "timetable.slot.read", school_wide=True)'

if t_target in t_text:
    t_text = t_text.replace(t_target, t_replacement, 1)
    with open(teachers_path, "w", encoding="utf-8") as f:
        f.write(t_text)
    print("2. teachers.py updated to allow timetable.slot.read for listing teachers.")
else:
    print("2. teachers.py already updated or target mismatch.")

# 3. Update seed.py to map coordinator to academic_coordinator
seed_path = os.path.join(backend_dir, "seed.py")
with open(seed_path, "r", encoding="utf-8") as f:
    s_text = f.read()

s_target = '            if user.login_id == TRANSPORT_INCHARGE_LOGIN'
s_replacement = '''            if user.login_id == TRANSPORT_INCHARGE_LOGIN
            else "academic_coordinator"
            if user.login_id in ("coordinator@sunrisepublic.edu", "coordinator")'''

if 'else "academic_coordinator"' not in s_text:
    assert s_target in s_text, "Target not found in seed.py"
    s_text = s_text.replace(s_target, s_replacement, 1)
    with open(seed_path, "w", encoding="utf-8") as f:
        f.write(s_text)
    print("3. seed.py updated to map coordinator to academic_coordinator.")
else:
    print("3. seed.py already updated.")

# 4. Update services/timetable.py to audit save_slot and arrange
svc_path = os.path.join(backend_dir, "app", "services", "timetable.py")
with open(svc_path, "r", encoding="utf-8") as f:
    svc_text = f.read()

# save_slot replacement
save_target = """    slot = None
    if slot_id:
        slot = db.get(TimetableSlot, slot_id)
        if slot is None or slot.school_id != school_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")
    if slot is None:
        slot = TimetableSlot(school_id=school_id, is_published=False)
        db.add(slot)
    slot.class_section_id = class_section_id
    slot.day_of_week = day_of_week
    slot.period_id = period_id
    slot.subject_id = subject_id
    slot.teacher_id = teacher_id
    slot.room = room.strip() if room and room.strip() else None
    db.flush()

    if overridable:
        audit.record(
            db,
            actor=actor,
            school_id=school_id,
            entity_type="timetable_slot",
            entity_id=slot.id,
            action=AuditAction.update,
            after={"override": [p["detail"] for p in overridable], "reason": override_reason},
        )
    return slot"""

save_replacement = """    slot = None
    is_new = True
    before_state = None
    if slot_id:
        slot = db.get(TimetableSlot, slot_id)
        if slot is None or slot.school_id != school_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")
        is_new = False
        before_state = {
            "class_section_id": slot.class_section_id,
            "day_of_week": slot.day_of_week.value if hasattr(slot.day_of_week, "value") else str(slot.day_of_week),
            "period_id": slot.period_id,
            "subject_id": slot.subject_id,
            "teacher_id": slot.teacher_id,
            "room": slot.room,
        }
    if slot is None:
        slot = TimetableSlot(school_id=school_id, is_published=False)
        db.add(slot)
    slot.class_section_id = class_section_id
    slot.day_of_week = day_of_week
    slot.period_id = period_id
    slot.subject_id = subject_id
    slot.teacher_id = teacher_id
    slot.room = room.strip() if room and room.strip() else None
    db.flush()

    audit.record(
        db,
        actor=actor,
        school_id=school_id,
        entity_type="timetable_slot",
        entity_id=slot.id,
        action=AuditAction.create if is_new else AuditAction.update,
        before=before_state,
        after={
            "class_section_id": class_section_id,
            "day_of_week": day_of_week.value if hasattr(day_of_week, "value") else str(day_of_week),
            "period_id": period_id,
            "subject_id": subject_id,
            "teacher_id": teacher_id,
            "room": slot.room,
            "override": [p["detail"] for p in overridable] if overridable else None,
        },
        reason=override_reason,
    )
    return slot"""

if "is_new = True" not in svc_text:
    assert save_target in svc_text, "save_target not found in timetable.py"
    svc_text = svc_text.replace(save_target, save_replacement, 1)

# arrange replacement
arrange_target = """    row = db.scalar(
        select(Substitution).where(
            Substitution.timetable_slot_id == slot.id, Substitution.date == on
        )
    )
    if row is None:
        row = Substitution(
            school_id=actor.school_id,
            timetable_slot_id=slot.id,
            date=on,
            absent_teacher_id=slot.teacher_id,
        )
        db.add(row)
    row.substitute_teacher_id = substitute_teacher_id
    row.reason = reason
    row.status = (
        SubstitutionStatus.assigned
        if substitute_teacher_id is not None
        else SubstitutionStatus.unfilled
    )
    db.commit()
    return row"""

arrange_replacement = """    row = db.scalar(
        select(Substitution).where(
            Substitution.timetable_slot_id == slot.id, Substitution.date == on
        )
    )
    is_new = row is None
    if row is None:
        row = Substitution(
            school_id=actor.school_id,
            timetable_slot_id=slot.id,
            date=on,
            absent_teacher_id=slot.teacher_id,
        )
        db.add(row)
    row.substitute_teacher_id = substitute_teacher_id
    row.reason = reason
    row.status = (
        SubstitutionStatus.assigned
        if substitute_teacher_id is not None
        else SubstitutionStatus.unfilled
    )
    db.flush()
    audit.record(
        db,
        actor=actor,
        school_id=actor.school_id,
        entity_type="substitution",
        entity_id=row.id,
        action=AuditAction.create if is_new else AuditAction.update,
        after={
            "slot_id": slot.id,
            "date": str(on),
            "absent_teacher_id": slot.teacher_id,
            "substitute_teacher_id": substitute_teacher_id,
            "reason": reason,
            "status": row.status.value if hasattr(row.status, "value") else str(row.status),
        },
    )
    db.commit()
    return row"""

if "entity_type=\"substitution\"" not in svc_text:
    assert arrange_target in svc_text, "arrange_target not found in timetable.py"
    svc_text = svc_text.replace(arrange_target, arrange_replacement, 1)

with open(svc_path, "w", encoding="utf-8") as f:
    f.write(svc_text)
print("4. services/timetable.py updated with audit logging.")

# 5. Update api/admin/timetable.py with audit logging for add_period, delete_slot, publish, unpublish
api_tt_path = os.path.join(backend_dir, "app", "api", "admin", "timetable.py")
with open(api_tt_path, "r", encoding="utf-8") as f:
    api_text = f.read()

# Add audit import to api/admin/timetable.py
if "from app.services import audit" not in api_text:
    api_text = api_text.replace("from app.services import timetable as svc", "from app.services import audit, timetable as svc")
    api_text = api_text.replace("    User,\n)", "    User,\n    AuditAction,\n)")

add_period_target = """    row = SchoolPeriod(school_id=user.school_id, **body.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id, "period_no": row.period_no}"""

add_period_replacement = """    row = SchoolPeriod(school_id=user.school_id, **body.model_dump())
    db.add(row)
    db.commit()
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="school_period",
        entity_id=row.id,
        action=AuditAction.create,
        after={
            "period_no": row.period_no,
            "start_time": str(row.start_time),
            "end_time": str(row.end_time),
            "name": row.name,
            "is_break": row.is_break,
        },
    )
    db.commit()
    return {"id": row.id, "period_no": row.period_no}"""

if "entity_type=\"school_period\"" not in api_text:
    assert add_period_target in api_text, "add_period_target not found"
    api_text = api_text.replace(add_period_target, add_period_replacement, 1)

pub_target = """@router.post("/publish", dependencies=[writer])
def publish_timetable(
    class_section_id: int | None = Query(None),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    count = svc.publish_timetable(db, user.school_id, class_section_id)
    db.commit()
    return {"published": True, "count": count}


@router.post("/unpublish", dependencies=[writer])
def unpublish_timetable(
    class_section_id: int | None = Query(None),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    count = svc.unpublish_timetable(db, user.school_id, class_section_id)
    db.commit()
    return {"published": False, "count": count}


@router.delete("/slots/{slot_id}", status_code=204, dependencies=[writer])
def delete_slot(
    slot_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> None:
    slot = db.get(TimetableSlot, slot_id)
    if slot is None or slot.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")
    db.delete(slot)
    db.commit()"""

pub_replacement = """@router.post("/publish", dependencies=[writer])
def publish_timetable(
    class_section_id: int | None = Query(None),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    count = svc.publish_timetable(db, user.school_id, class_section_id)
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="timetable",
        action=AuditAction.publish,
        after={"published": True, "count": count, "class_section_id": class_section_id},
    )
    db.commit()
    return {"published": True, "count": count}


@router.post("/unpublish", dependencies=[writer])
def unpublish_timetable(
    class_section_id: int | None = Query(None),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    count = svc.unpublish_timetable(db, user.school_id, class_section_id)
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="timetable",
        action=AuditAction.status_change,
        after={"published": False, "count": count, "class_section_id": class_section_id},
    )
    db.commit()
    return {"published": False, "count": count}


@router.delete("/slots/{slot_id}", status_code=204, dependencies=[writer])
def delete_slot(
    slot_id: int, user: User = Depends(reader), db: Session = Depends(get_db)
) -> None:
    slot = db.get(TimetableSlot, slot_id)
    if slot is None or slot.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")
    before_data = {
        "class_section_id": slot.class_section_id,
        "day_of_week": slot.day_of_week.value if hasattr(slot.day_of_week, "value") else str(slot.day_of_week),
        "period_id": slot.period_id,
        "subject_id": slot.subject_id,
        "teacher_id": slot.teacher_id,
        "room": slot.room,
    }
    db.delete(slot)
    audit.record(
        db,
        actor=user,
        school_id=user.school_id,
        entity_type="timetable_slot",
        entity_id=slot_id,
        action=AuditAction.delete,
        before=before_data,
    )
    db.commit()"""

if "entity_type=\"timetable\"" not in api_text:
    assert pub_target in api_text, "pub_target not found in timetable.py"
    api_text = api_text.replace(pub_target, pub_replacement, 1)

with open(api_tt_path, "w", encoding="utf-8") as f:
    f.write(api_text)
print("5. api/admin/timetable.py updated with audit logging.")
