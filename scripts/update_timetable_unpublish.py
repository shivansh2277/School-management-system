from pathlib import Path

path = Path("backend/app/api/admin/timetable.py")
content = path.read_text(encoding="utf-8")

old_text = """@router.post("/unpublish", dependencies=[writer])
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
    )"""

new_text = """@router.post("/unpublish", dependencies=[writer])
def unpublish_timetable(
    class_section_id: int | None = Query(None),
    reason: str | None = Query(None),
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
        reason=reason or "Timetable reverted to draft",
    )"""

if old_text in content:
    content = content.replace(old_text, new_text, 1)
    path.write_text(content, encoding="utf-8")
    print("Replaced LF version successfully.")
elif old_text.replace("\n", "\r\n") in content:
    content = content.replace(old_text.replace("\n", "\r\n"), new_text.replace("\n", "\r\n"), 1)
    path.write_text(content, encoding="utf-8")
    print("Replaced CRLF version successfully.")
else:
    print("Could not find old_text in content!")
