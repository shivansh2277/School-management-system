"""Tests for Session 6: Database Schema Refactoring (enrolment_id).

Validates:
1. Physical column existence, types, and removal of old student_id columns.
2. Unique constraints on (exam_schedule_id, enrolment_id) and (homework_id, enrolment_id).
3. ON DELETE integrity:
   - Marks: RESTRICT (deleting enrolment with marks raises IntegrityError).
   - HomeworkSubmission: CASCADE (deleting enrolment deletes submissions).
   - Grievance: SET NULL (deleting enrolment sets grievance.enrolment_id = NULL).
4. Backfill integrity: all seeded marks, homework submissions, and grievances point to valid enrolments.
5. Hybrid properties: Mark.student_id and HomeworkSubmission.student_id resolve correctly.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.models import (
    Enrolment,
    ExamSchedule,
    Grievance,
    Homework,
    HomeworkSubmission,
    Mark,
    Student,
)


def test_migration_columns_exist_and_student_id_removed(db):
    """Verify schema modifications: enrolment_id present, student_id removed from physical tables."""
    inspector = inspect(db.get_bind())

    # Marks table
    mark_cols = {c["name"]: c for c in inspector.get_columns("marks")}
    assert "enrolment_id" in mark_cols, "marks must have enrolment_id"
    assert "student_id" not in mark_cols, "marks must NOT have physical student_id column"

    # Homework submissions table
    sub_cols = {c["name"]: c for c in inspector.get_columns("homework_submissions")}
    assert "enrolment_id" in sub_cols, "homework_submissions must have enrolment_id"
    assert "student_id" not in sub_cols, "homework_submissions must NOT have physical student_id column"
    assert "marks" in sub_cols, "homework_submissions must have marks column"
    assert "remarks" in sub_cols, "homework_submissions must have remarks column"
    assert "graded_at" in sub_cols, "homework_submissions must have graded_at column"
    assert "attachment_url" in sub_cols, "homework_submissions must have attachment_url column"

    # Homework table
    hw_cols = {c["name"]: c for c in inspector.get_columns("homework")}
    assert "attachment_url" in hw_cols, "homework must have attachment_url column"

    # Grievances table
    grievance_cols = {c["name"]: c for c in inspector.get_columns("grievances")}
    assert "enrolment_id" in grievance_cols, "grievances must have enrolment_id column"


def test_unique_constraint_marks(db, ids):
    """Assert UniqueConstraint('exam_schedule_id', 'enrolment_id') triggers IntegrityError on duplicate."""
    p = db.query(ExamSchedule).filter(ExamSchedule.class_section_id == ids["section_10a"]).first()
    enr = db.scalar(
        select(Enrolment).where(
            Enrolment.student_id == ids["student_1"],
            Enrolment.class_section_id == ids["section_10a"],
        )
    )
    assert p is not None and enr is not None

    # First mark insertion
    existing = db.scalar(
        select(Mark).where(Mark.exam_schedule_id == p.id, Mark.enrolment_id == enr.id)
    )
    if not existing:
        db.add(
            Mark(
                school_id=ids["school"],
                exam_schedule_id=p.id,
                enrolment_id=enr.id,
                marks_obtained=Decimal("45.0"),
                entered_by=1,
            )
        )
        db.flush()

    # Duplicate mark insertion must raise IntegrityError
    dup = Mark(
        school_id=ids["school"],
        exam_schedule_id=p.id,
        enrolment_id=enr.id,
        marks_obtained=Decimal("40.0"),
        entered_by=1,
    )
    db.add(dup)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_unique_constraint_homework_submission(db, ids):
    """Assert UniqueConstraint('homework_id', 'enrolment_id') triggers IntegrityError on duplicate."""
    hw = db.query(Homework).filter(Homework.class_section_id == ids["section_10a"]).first()
    enr = db.scalar(
        select(Enrolment).where(
            Enrolment.student_id == ids["student_1"],
            Enrolment.class_section_id == ids["section_10a"],
        )
    )
    assert hw is not None and enr is not None

    existing = db.scalar(
        select(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == hw.id,
            HomeworkSubmission.enrolment_id == enr.id,
        )
    )
    if not existing:
        db.add(
            HomeworkSubmission(
                school_id=ids["school"],
                homework_id=hw.id,
                enrolment_id=enr.id,
                answer_text="Initial submission",
                submitted_at=datetime.now(UTC),
            )
        )
        db.flush()

    # Duplicate submission row
    dup = HomeworkSubmission(
        school_id=ids["school"],
        homework_id=hw.id,
        enrolment_id=enr.id,
        answer_text="Duplicate submission",
        submitted_at=datetime.now(UTC),
    )
    db.add(dup)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_on_delete_cascade_homework_submissions(db, ids):
    """Deleting an enrolment must cascade-delete its homework submissions."""
    from sqlalchemy import text
    if db.bind.dialect.name == "sqlite":
        db.execute(text("PRAGMA foreign_keys = ON;"))

    student = Student(school_id=ids["school"], user_id=1, admission_no="DUMMY_S999")
    db.add(student)
    db.flush()

    enrolment = Enrolment(
        school_id=ids["school"],
        student_id=student.id,
        academic_year_id=ids["year"],
        class_section_id=ids["section_10a"],
        roll_no=999,
    )
    db.add(enrolment)
    db.flush()

    hw = db.query(Homework).filter(Homework.class_section_id == ids["section_10a"]).first()
    sub = HomeworkSubmission(
        school_id=ids["school"],
        homework_id=hw.id,
        enrolment_id=enrolment.id,
        answer_text="Dummy answer",
        submitted_at=datetime.now(UTC),
    )
    db.add(sub)
    db.flush()
    sub_id = sub.id

    # Delete enrolment
    db.delete(enrolment)
    db.flush()
    db.expire_all()

    # Sub must be deleted
    assert db.get(HomeworkSubmission, sub_id) is None


def test_on_delete_restrict_marks(db, ids):
    """Deleting an enrolment with linked marks must be prevented (RESTRICT)."""
    from sqlalchemy import text
    if db.bind.dialect.name == "sqlite":
        db.execute(text("PRAGMA foreign_keys = ON;"))

    student = Student(school_id=ids["school"], user_id=1, admission_no="DUMMY_S998")
    db.add(student)
    db.flush()

    enrolment = Enrolment(
        school_id=ids["school"],
        student_id=student.id,
        academic_year_id=ids["year"],
        class_section_id=ids["section_10a"],
        roll_no=998,
    )
    db.add(enrolment)
    db.flush()

    p = db.query(ExamSchedule).filter(ExamSchedule.class_section_id == ids["section_10a"]).first()
    mark = Mark(
        school_id=ids["school"],
        exam_schedule_id=p.id,
        enrolment_id=enrolment.id,
        marks_obtained=Decimal("50.0"),
        entered_by=1,
    )
    db.add(mark)
    db.flush()

    # Deleting enrolment with marks must fail
    db.delete(enrolment)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_on_delete_set_null_grievance(db, ids):
    """Deleting an enrolment linked to a grievance sets grievance.enrolment_id = NULL."""
    from sqlalchemy import text
    if db.bind.dialect.name == "sqlite":
        db.execute(text("PRAGMA foreign_keys = ON;"))

    student = Student(school_id=ids["school"], user_id=1, admission_no="DUMMY_S997")
    db.add(student)
    db.flush()

    enrolment = Enrolment(
        school_id=ids["school"],
        student_id=student.id,
        academic_year_id=ids["year"],
        class_section_id=ids["section_10a"],
        roll_no=997,
    )
    db.add(enrolment)
    db.flush()

    grievance = Grievance(
        school_id=ids["school"],
        title="Test Grievance",
        description="Testing set null on delete",
        category="academic",
        raised_by_id=1,
        raised_by_role="admin",
        raised_by_name="Admin",
        student_id=student.id,
        enrolment_id=enrolment.id,
    )
    db.add(grievance)
    db.flush()
    gid = grievance.id

    db.delete(enrolment)
    db.flush()
    db.expire_all()

    refetched = db.get(Grievance, gid)
    assert refetched is not None
    assert refetched.enrolment_id is None
    assert refetched.student_id == student.id


def test_backfill_integrity(db):
    """All existing marks, homework submissions, and grievances have valid enrolment_ids."""
    # Marks
    marks = list(db.scalars(select(Mark)))
    assert len(marks) > 0, "Seeded database must have marks"
    for m in marks:
        assert m.enrolment_id is not None
        enr = db.get(Enrolment, m.enrolment_id)
        assert enr is not None
        assert m.student_id == enr.student_id

    # Homework submissions
    submissions = list(db.scalars(select(HomeworkSubmission)))
    assert len(submissions) > 0, "Seeded database must have homework submissions"
    for s in submissions:
        assert s.enrolment_id is not None
        enr = db.get(Enrolment, s.enrolment_id)
        assert enr is not None
        assert s.student_id == enr.student_id

    # Grievances with students
    grievances = list(db.scalars(select(Grievance).where(Grievance.student_id.is_not(None))))
    for g in grievances:
        assert g.enrolment_id is not None
        enr = db.get(Enrolment, g.enrolment_id)
        assert enr is not None
        assert enr.student_id == g.student_id


def test_hybrid_property_querying(db, ids):
    """Mark.student_id and HomeworkSubmission.student_id can be filtered in queries."""
    marks = list(
        db.scalars(select(Mark).where(Mark.student_id == ids["student_1"]))
    )
    assert len(marks) > 0

    subs = list(
        db.scalars(select(HomeworkSubmission).where(HomeworkSubmission.student_id == ids["student_1"]))
    )
    assert len(subs) > 0
