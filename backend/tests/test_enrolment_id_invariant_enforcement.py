"""Strict verification of the enrolment_id architectural invariant.

Verifies that backward compatibility mechanisms:
1. Are strictly read-only or input-translation only.
2. Cannot be used to bypass the enrolment_id requirement at the DB / ORM level.
3. Cannot bypass class section / academic year scoping when student_id is provided in input.
4. Guarantee that all internal mutations are strictly executed against verified enrolment_id.
"""
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    Attendance,
    ClassSection,
    ClassSubjectTeacher,
    Employee,
    Enrolment,
    EnrolmentStatus,
    ExamSchedule,
    Homework,
    HomeworkSubmission,
    Mark,
    User,
)


def test_mark_student_id_is_strictly_read_only(db):
    """Mark.student_id is a hybrid property with no setter and cannot be assigned to."""
    mark = db.query(Mark).first()
    assert mark is not None

    # Read works via the hybrid property
    assert mark.student_id == mark.enrolment.student_id

    # Attempting to assign to student_id raises AttributeError
    with pytest.raises(AttributeError, match="can't set attribute"):
        mark.student_id = 99999


def test_cannot_instantiate_or_persist_mark_with_student_id(db):
    """Mark cannot be instantiated with student_id and cannot be persisted without enrolment_id."""
    sched = db.query(ExamSchedule).first()

    # Instantiating Mark with student_id fails with AttributeError because student_id has no setter
    with pytest.raises(AttributeError, match="can't set attribute"):
        Mark(
            school_id=sched.school_id,
            exam_schedule_id=sched.id,
            student_id=1,
            marks_obtained=Decimal("50.00"),
            entered_by=1,
        )

    # Directly attempting to insert a mark without enrolment_id raises IntegrityError / NotNullViolation
    invalid_mark = Mark(
        school_id=sched.school_id,
        exam_schedule_id=sched.id,
        marks_obtained=Decimal("50.00"),
        entered_by=1,
    )
    db.add(invalid_mark)
    with pytest.raises((IntegrityError, Exception)):
        db.flush()
    db.rollback()


def test_homework_submission_cannot_be_instantiated_with_student_id(db):
    """HomeworkSubmission cannot be instantiated with student_id; enrolment_id is mandatory."""
    hw = db.query(Homework).first()

    # AttributeError because student_id has no setter
    with pytest.raises(AttributeError, match="can't set attribute"):
        HomeworkSubmission(
            school_id=hw.school_id,
            homework_id=hw.id,
            student_id=1,
            answer_text="Sample",
            submitted_at=datetime.now(UTC),
        )

    # Omission of enrolment_id fails database NOT NULL constraint
    invalid_sub = HomeworkSubmission(
        school_id=hw.school_id,
        homework_id=hw.id,
        answer_text="Sample",
        submitted_at=datetime.now(UTC),
    )
    db.add(invalid_sub)
    with pytest.raises((IntegrityError, Exception)):
        db.flush()
    db.rollback()


def test_attendance_has_no_student_id_column(db):
    """Attendance has no student_id column or attribute; enrolment_id is mandatory."""
    with pytest.raises(TypeError):
        Attendance(
            school_id=1,
            student_id=1,
            date=date.today(),
            status="P",
        )


def test_input_student_id_cannot_bypass_section_scoping_in_marks(client, teacher, db):
    """Passing a valid student_id of a student enrolled in a DIFFERENT class section

    is strictly blocked and cannot write marks to the paper.
    """
    # Teacher fixture is TCH001 (Anita Sharma)
    teacher_user = db.query(User).filter(User.login_id == "TCH001").first()
    teacher_emp = db.query(Employee).filter(Employee.user_id == teacher_user.id).first()

    # Find a paper taught by this teacher
    cst = db.query(ClassSubjectTeacher).filter(ClassSubjectTeacher.teacher_id == teacher_emp.id).first()
    sched = (
        db.query(ExamSchedule)
        .filter(
            ExamSchedule.class_section_id == cst.class_section_id,
            ExamSchedule.subject_id == cst.subject_id,
        )
        .first()
    )
    sec1_id = sched.class_section_id

    # Find a student who is NOT in this section (e.g. in another section)
    other_enr = (
        db.query(Enrolment)
        .filter(
            Enrolment.school_id == sched.school_id,
            Enrolment.class_section_id != sec1_id,
            Enrolment.status == EnrolmentStatus.active,
        )
        .first()
    )
    assert other_enr is not None
    out_of_section_student_id = other_enr.student_id

    # Attempting to submit marks using student_id of the out-of-section student
    res = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": sched.id,
            "entries": [{"student_id": out_of_section_student_id, "marks_obtained": "75"}],
        },
        headers=teacher,
    )
    # Must be forbidden (403) or rejected (422)
    assert res.status_code in (403, 422)

    # Verify no mark was written for this student or other_enr
    persisted = (
        db.query(Mark)
        .filter(
            Mark.exam_schedule_id == sched.id,
            Mark.enrolment_id == other_enr.id,
        )
        .first()
    )
    assert persisted is None


def test_input_student_id_cannot_bypass_section_scoping_in_attendance(client, teacher, db):
    """Passing a student_id of an out-of-section student in attendance roll call

    is strictly blocked and does not create an attendance record.
    """
    teacher_user = db.query(User).filter(User.login_id == "TCH001").first()
    teacher_emp = db.query(Employee).filter(Employee.user_id == teacher_user.id).first()
    sec = db.query(ClassSection).filter(ClassSection.class_teacher_id == teacher_emp.id).first()

    # Student not in this section
    other_enr = (
        db.query(Enrolment)
        .filter(
            Enrolment.school_id == sec.school_id,
            Enrolment.class_section_id != sec.id,
            Enrolment.status == EnrolmentStatus.active,
        )
        .first()
    )
    assert other_enr is not None

    res = client.post(
        "/teacher/attendance",
        json={
            "class_section_id": sec.id,
            "date": str(date.today()),
            "entries": [{"student_id": other_enr.student_id, "status": "P"}],
        },
        headers=teacher,
    )
    assert res.status_code in (403, 422)

    # Assert no attendance record was created for other_enr
    persisted = (
        db.query(Attendance)
        .filter(
            Attendance.enrolment_id == other_enr.id,
            Attendance.date == date.today(),
        )
        .first()
    )
    assert persisted is None


def test_input_student_id_strictly_resolves_to_current_enrolment(client, teacher, db):
    """When a legitimate student_id is sent for backward compatibility, the service

    resolves it to the specific section enrolment and writes that enrolment_id to DB.
    """
    teacher_user = db.query(User).filter(User.login_id == "TCH001").first()
    teacher_emp = db.query(Employee).filter(Employee.user_id == teacher_user.id).first()

    cst = db.query(ClassSubjectTeacher).filter(ClassSubjectTeacher.teacher_id == teacher_emp.id).first()
    sched = (
        db.query(ExamSchedule)
        .filter(
            ExamSchedule.class_section_id == cst.class_section_id,
            ExamSchedule.subject_id == cst.subject_id,
        )
        .first()
    )
    enr = (
        db.query(Enrolment)
        .filter(
            Enrolment.class_section_id == sched.class_section_id,
            Enrolment.status == EnrolmentStatus.active,
        )
        .first()
    )
    assert enr is not None

    # Post using student_id
    res = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": sched.id,
            "entries": [{"student_id": enr.student_id, "marks_obtained": str(min(Decimal("25.00"), sched.max_marks))}],
        },
        headers=teacher,
    )
    assert res.status_code == 200

    # Verify directly in the database that the row holds enrolment_id
    persisted = (
        db.query(Mark)
        .filter(
            Mark.exam_schedule_id == sched.id,
            Mark.enrolment_id == enr.id,
        )
        .first()
    )
    assert persisted is not None
    assert persisted.enrolment_id == enr.id
    assert persisted.marks_obtained == min(Decimal("25.00"), sched.max_marks)
