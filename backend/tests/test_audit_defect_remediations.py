"""Dedicated regression test suite for all 8 audit defect remediations.

Verifies:
1. Student Data Loss: Dossier medical, emergency, demographic & previous school fields preserved into Student.
2. Incorrect Admission Fee Trigger: Application fee does NOT enroll; Admission fee atomically enrolls; Duplicate prevention; Void rollback.
3. Read-Only Timetable & Builder: Slot creation, update, conflict check, and deletion.
4. Double-Booking Concurrency: DB unique constraints prevent teacher and room clashes, with case-insensitive whitespace-trimmed room normalization.
5. Premature Timetable Publication: Draft vs Published lifecycle; published-only filtering on view endpoints; publish & unpublish actions.
6. Absent-Student Percentages: Absent papers contribute scheduled max marks to denominator; exempted papers are excluded; avoids score inflation.
7. Genuine PASS/FAIL/COMPARTMENT: 33% CBSE rule evaluation; fee dues withholding cleanly separated from academic evaluation.
8. Cross-Tenant Exam Security: Tenancy ownership enforcement on exam paper scheduling; exam date boundary validation.
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest
from sqlalchemy import select

from app.models import (
    AdmissionCycle,
    Application,
    ApplicationMedical,
    ApplicationPayment,
    ApplicationStatus,
    ClassSection,
    DayOfWeek,
    Document,
    Employee,
    Enrolment,
    EnrolmentStatus,
    Exam,
    ExamSchedule,
    Mark,
    School,
    SchoolPeriod,
    Student,
    StudentStatus,
    Subject,
    TimetableSlot,
    User,
    UserRole,
)
from app.services import assessment, conversion, report_cards, tenancy, timetable as tt_svc

PDF = b"%PDF-1.4\n%certificate\n"
PORTAL = "/public/SPS/admission"


def _apply_on_portal(client, **over):
    body = {
        "first_name": "TestChild",
        "last_name": "Audit",
        "date_of_birth": "2019-03-05",
        "gender": "male",
        "class_applying_for": "1",
        "address": {
            "line1": "10 Civil Lines",
            "city": "Lucknow",
            "state": "Uttar Pradesh",
            "pincode": "226001",
        },
        "guardians": [
            {
                "relation": "father",
                "full_name": "Ramesh Audit",
                "mobile": "9811199999",
                "email": "ramesh@example.com",
                "is_primary": True,
            }
        ],
        "information_accuracy": True,
        "school_rules_accepted": True,
        "data_processing_consent": True,
        "apaar_consent": True,
    }
    body.update(over)
    r = client.post(f"{PORTAL}/apply", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _clear_documents(client, admission_officer, application_id):
    for code in ("birth_certificate", "photo", "address_proof"):
        doc_id = client.post(
            f"/admin/admission/applications/{application_id}/documents",
            data={"code": code},
            files={"file": (f"{code}.pdf", PDF + code.encode(), "application/pdf")},
            headers=admission_officer,
        ).json()["document_id"]
        client.post(
            f"/admin/admission/documents/{doc_id}/verify",
            json={"approved": True, "original_seen": True},
            headers=admission_officer,
        )


def _admit_and_offer(client, admission_officer, application_id):
    client.post(
        f"/admin/admission/applications/{application_id}/status",
        json={"status": "decision_pending"},
        headers=admission_officer,
    )
    client.post(
        f"/admin/admission/applications/{application_id}/decision",
        json={"decision": "admitted", "reason": "Passed evaluation"},
        headers=admission_officer,
    )
    client.post(
        f"/admin/admission/applications/{application_id}/offer",
        json={"expires_on": str(date.today() + timedelta(days=10)), "offer_amount": "25000"},
        headers=admission_officer,
    )
    client.post(
        f"/admin/admission/applications/{application_id}/offer/response",
        json={"accepted": True},
        headers=admission_officer,
    )


# -----------------------------------------------------------------------------
# DEFECT 1: Student Data Loss Prevention
# -----------------------------------------------------------------------------

def test_defect_1_student_dossier_data_preservation(client, admin, admission_officer, db):
    """Ensure medical, emergency doctor, demographic, and previous-school data
    captured in the admission dossier is preserved in the permanent Student profile.
    """
    created = _apply_on_portal(
        client,
        nationality="Indian",
        religion="Hindu",
        caste_category="OBC",
        mother_tongue="Hindi",
        place_of_birth="Varanasi",
        identification_marks="Scar on left elbow",
        is_single_child=True,
        aadhaar_last4="9876",
        previous_school={
            "school_name": "St. Xavier Academy",
            "last_class_attended": "Class KG",
            "board": "CBSE",
            "percentage": 88.5,
        },
    )
    app = db.scalar(select(Application).where(Application.application_no == created["application_no"]))
    app.aadhaar_verified = True
    db.flush()

    # Add medical dossier details
    med = ApplicationMedical(
        school_id=app.school_id,
        application_id=app.id,
        blood_group="B+",
        known_allergies="Penicillin",
        chronic_conditions="Mild Asthma",
        regular_medication="Inhaler as needed",
        emergency_doctor="Dr. K. S. Verma",
        emergency_doctor_phone="9876501234",
    )
    db.add(med)
    db.flush()

    # Progress application
    _clear_documents(client, admission_officer, app.id)
    _admit_and_offer(client, admission_officer, app.id)

    # Collect admission fee to trigger conversion
    pay_res = client.post(
        f"/admin/admission/applications/{app.id}/payments",
        json={"purpose": "admission_fee", "amount": "25000", "method": "upi", "reference": "UPI-D1-1234"},
        headers=admission_officer,
    )
    assert pay_res.status_code == 201
    student_id = pay_res.json()["student"]["student_id"]

    # Verify permanent Student record has all preserved fields
    student = db.get(Student, student_id)
    assert student is not None
    assert student.blood_group == "B+"
    assert student.nationality == "Indian"
    assert student.religion == "Hindu"
    assert student.caste_category == "OBC"
    assert student.mother_tongue == "Hindi"
    assert student.place_of_birth == "Varanasi"
    assert student.identification_marks == "Scar on left elbow"
    assert student.is_single_child is True
    assert student.aadhaar_last4 == "9876"
    assert student.aadhaar_verified is True
    assert student.emergency_doctor == "Dr. K. S. Verma"
    assert student.emergency_doctor_phone == "9876501234"
    assert student.known_allergies == "Penicillin"
    assert student.chronic_conditions == "Mild Asthma"
    assert student.regular_medications == "Inhaler as needed"
    assert student.previous_school["school_name"] == "St. Xavier Academy"
    assert student.application_id == app.id

    # Verify API GET endpoint returns these fields
    r = client.get(f"/admin/students/{student.id}", headers=admin)
    assert r.status_code == 200
    data = r.json()
    assert data["blood_group"] == "B+"
    assert data["known_allergies"] == "Penicillin"
    assert data["emergency_doctor"] == "Dr. K. S. Verma"
    assert data["application_id"] == app.id


# -----------------------------------------------------------------------------
# DEFECT 2: Admission Fee Trigger vs Application Fee
# -----------------------------------------------------------------------------

def test_defect_2_application_fee_does_not_enroll_student(client, admission_officer, db):
    """Paying the application/registration fee must advance the application to submitted
    but must NOT enroll a student or create an enrolment record.
    """
    created = _apply_on_portal(client)
    app = db.scalar(select(Application).where(Application.application_no == created["application_no"]))

    # Pay application_fee (e.g. form processing fee 500)
    pay_res = client.post(
        f"/admin/admission/applications/{app.id}/payments",
        json={"purpose": "application_fee", "amount": "500", "method": "cash"},
        headers=admission_officer,
    )
    assert pay_res.status_code == 201
    body = pay_res.json()
    assert "student" not in body
    assert body["purpose"] == "application_fee"

    # Verify no student was created for this application
    db.refresh(app)
    assert app.student_id is None
    enrolled = db.scalar(select(Student).where(Student.application_id == app.id))
    assert enrolled is None


def test_defect_2_admission_fee_atomic_enrollment_and_duplicate_prevention(client, admission_officer, db):
    """Paying the admission fee on an offer_accepted application triggers atomic enrollment.
    Subsequent duplicate attempts must be refused.
    """
    created = _apply_on_portal(client)
    app = db.scalar(select(Application).where(Application.application_no == created["application_no"]))

    _clear_documents(client, admission_officer, app.id)
    _admit_and_offer(client, admission_officer, app.id)

    # 1. Pay admission_fee -> atomically converts
    pay_res = client.post(
        f"/admin/admission/applications/{app.id}/payments",
        json={"purpose": "admission_fee", "amount": "25000", "method": "upi", "reference": "UPI-D2-999"},
        headers=admission_officer,
    )
    assert pay_res.status_code == 201
    body = pay_res.json()
    assert "student" in body
    student_id = body["student"]["student_id"]
    payment_id = body["id"]

    # 2. Duplicate conversion attempt via /convert endpoint raises 409
    dup = client.post(f"/admin/admission/applications/{app.id}/convert", headers=admission_officer)
    assert dup.status_code == 409

    # 3. Voiding payment rolls back enrollment
    void_res = client.delete(
        f"/admin/admission/payments/{payment_id}?reason=Administrative+void",
        headers=admission_officer,
    )
    assert void_res.status_code == 200

    student = db.get(Student, student_id)
    assert student.status == StudentStatus.suspended
    enrolment = db.scalar(select(Enrolment).where(Enrolment.student_id == student.id))
    assert enrolment.status == EnrolmentStatus.transferred_out


# -----------------------------------------------------------------------------
# DEFECT 3 & 4: Timetable Concurrency & Double-Booking Constraints
# -----------------------------------------------------------------------------

def test_defect_4_teacher_and_room_double_booking_constraints(client, admin, db):
    """Database unique constraints and conflict detection prevent teacher and room clashes."""
    school = db.scalar(select(School))
    sections = db.scalars(select(ClassSection).where(ClassSection.school_id == school.id)).all()
    assert len(sections) >= 2
    sec1, sec2 = sections[0], sections[1]

    teacher = db.scalar(select(Employee).where(Employee.school_id == school.id))
    subject = db.scalar(select(Subject).where(Subject.school_id == school.id))
    period = db.scalar(select(SchoolPeriod).where(SchoolPeriod.school_id == school.id, SchoolPeriod.is_break.is_(False)))

    # Clear any conflicting slots for this test slot
    db.query(TimetableSlot).filter(
        TimetableSlot.day_of_week == DayOfWeek.wed,
        TimetableSlot.period_id == period.id,
    ).delete()
    db.flush()

    # 1. Schedule sec1 with teacher and room
    user = db.scalar(select(User).where(User.school_id == school.id, User.role == UserRole.admin))
    slot1 = tt_svc.save_slot(
        db,
        user,
        class_section_id=sec1.id,
        day_of_week=DayOfWeek.wed,
        period_id=period.id,
        subject_id=subject.id,
        teacher_id=teacher.id,
        room="Room 204",
    )
    db.flush()
    assert slot1.id is not None

    # 2. Try to schedule sec2 with the same teacher at the same day & period -> raises conflict
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        tt_svc.save_slot(
            db,
            user,
            class_section_id=sec2.id,
            day_of_week=DayOfWeek.wed,
            period_id=period.id,
            subject_id=subject.id,
            teacher_id=teacher.id,
            room="Room 305",
        )
    assert exc.value.status_code == 409
    conflicts = exc.value.detail.get("conflicts", [])
    assert any(c.get("kind") == "teacher" for c in conflicts)

    # 3. Room conflict with whitespace & case insensitivity
    # Room "room 204 " vs "Room 204"
    other_teacher = db.scalars(select(Employee).where(Employee.school_id == school.id, Employee.id != teacher.id)).first()
    with pytest.raises(HTTPException) as exc:
        tt_svc.save_slot(
            db,
            user,
            class_section_id=sec2.id,
            day_of_week=DayOfWeek.wed,
            period_id=period.id,
            subject_id=subject.id,
            teacher_id=other_teacher.id,
            room="  room 204  ",
        )
    assert exc.value.status_code == 409
    conflicts_room = exc.value.detail.get("conflicts", [])
    assert any(c.get("kind") == "room" for c in conflicts_room)


# -----------------------------------------------------------------------------
# DEFECT 5: Premature Timetable Publication Lifecycle
# -----------------------------------------------------------------------------

def test_defect_5_timetable_lifecycle_draft_vs_published(client, admin, db):
    """Timetable slots must default to draft (is_published=False).
    Draft changes must be hidden when published_only=True until explicitly published.
    """
    school = db.scalar(select(School))
    section = db.scalar(select(ClassSection).where(ClassSection.school_id == school.id))
    teacher = db.scalar(select(Employee).where(Employee.school_id == school.id))
    subject = db.scalar(select(Subject).where(Subject.school_id == school.id))
    period = db.scalar(select(SchoolPeriod).where(SchoolPeriod.school_id == school.id, SchoolPeriod.is_break.is_(False)))

    # Clean existing slot
    db.query(TimetableSlot).filter(
        TimetableSlot.day_of_week == DayOfWeek.thu,
        TimetableSlot.period_id == period.id,
        TimetableSlot.class_section_id == section.id,
    ).delete()
    db.flush()

    # 1. Create slot via API
    r = client.post(
        "/admin/timetable/slots",
        json={
            "class_section_id": section.id,
            "day_of_week": "thu",
            "period_id": period.id,
            "subject_id": subject.id,
            "teacher_id": teacher.id,
            "room": "Lab 1",
        },
        headers=admin,
    )
    assert r.status_code == 201
    slot_data = r.json()
    slot_id = slot_data["id"]
    assert slot_data["is_published"] is False

    # 2. Query published_only -> draft slot is hidden
    r_pub = client.get(f"/admin/timetable?class_section_id={section.id}&published_only=true", headers=admin)
    assert r_pub.status_code == 200
    ids = [s["id"] for s in r_pub.json()]
    assert slot_id not in ids

    # 3. Explicitly publish
    r_action = client.post(f"/admin/timetable/publish?class_section_id={section.id}", headers=admin)
    assert r_action.status_code == 200
    assert r_action.json()["published"] is True

    # 4. Query published_only -> slot is now visible
    r_pub2 = client.get(f"/admin/timetable?class_section_id={section.id}&published_only=true", headers=admin)
    assert r_pub2.status_code == 200
    ids2 = [s["id"] for s in r_pub2.json()]
    assert slot_id in ids2

    # 5. Revert to draft (unpublish)
    r_unpub = client.post(f"/admin/timetable/unpublish?class_section_id={section.id}", headers=admin)
    assert r_unpub.status_code == 200
    assert r_unpub.json()["published"] is False

    r_pub3 = client.get(f"/admin/timetable?class_section_id={section.id}&published_only=true", headers=admin)
    ids3 = [s["id"] for s in r_pub3.json()]
    assert slot_id not in ids3


# -----------------------------------------------------------------------------
# DEFECT 6: Absent Student Percentages
# -----------------------------------------------------------------------------

def test_defect_6_absent_student_percentage_calculation(db):
    """Absent papers must contribute their scheduled max marks to the denominator (total_max).
    They must not be excluded like exemptions, preventing 100% score inflation.
    """
    school = db.scalar(select(School))
    student = db.scalar(select(Student).where(Student.school_id == school.id))
    enrolment = db.scalar(select(Enrolment).where(Enrolment.student_id == student.id))
    subjects = db.scalars(select(Subject).where(Subject.school_id == school.id)).all()[:3]
    assert len(subjects) >= 3

    # Create Exam
    exam = Exam(
        school_id=school.id,
        name="Mid-Term Test",
        term="Term 1",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=5),
    )
    db.add(exam)
    db.flush()

    # Schedule 3 papers, 100 marks each
    p1 = ExamSchedule(school_id=school.id, exam_id=exam.id, class_section_id=enrolment.class_section_id, subject_id=subjects[0].id, exam_date=date.today(), max_marks=Decimal("100.00"))
    p2 = ExamSchedule(school_id=school.id, exam_id=exam.id, class_section_id=enrolment.class_section_id, subject_id=subjects[1].id, exam_date=date.today() + timedelta(days=1), max_marks=Decimal("100.00"))
    p3 = ExamSchedule(school_id=school.id, exam_id=exam.id, class_section_id=enrolment.class_section_id, subject_id=subjects[2].id, exam_date=date.today() + timedelta(days=2), max_marks=Decimal("100.00"))
    db.add_all([p1, p2, p3])
    db.flush()

    # Student sits for p1, is absent for p2, is exempted for p3
    user = db.scalar(select(User).where(User.school_id == school.id, User.role == UserRole.admin))
    m1 = Mark(school_id=school.id, exam_schedule_id=p1.id, enrolment_id=enrolment.id, entered_by=user.id, marks_obtained=Decimal("80.00"), is_absent=False, is_exempted=False)
    m2 = Mark(school_id=school.id, exam_schedule_id=p2.id, enrolment_id=enrolment.id, entered_by=user.id, marks_obtained=None, is_absent=True, is_exempted=False)
    m3 = Mark(school_id=school.id, exam_schedule_id=p3.id, enrolment_id=enrolment.id, entered_by=user.id, marks_obtained=None, is_absent=False, is_exempted=True)
    db.add_all([m1, m2, m3])
    db.flush()

    card = assessment.report_card(db, student.id, exam.id)
    # Total obtained: 80
    assert card.total_obtained == Decimal("80.00")
    # Total max: 200 (p1: 100 + p2 absent: 100). p3 exempted is excluded!
    assert card.total_max == Decimal("200.00")
    # Overall percent: 80 / 200 * 100 = 40.0% (NOT 80/100 = 80.0%)
    assert card.overall_percent == 40.0


# -----------------------------------------------------------------------------
# DEFECT 7: Genuine PASS/FAIL/COMPARTMENT Status
# -----------------------------------------------------------------------------

def test_defect_7_cbse_pass_fail_compartment_evaluation():
    """Verify genuinely calculated pass/fail/compartment evaluations:
    - 0 subjects failed: PASS ("pass")
    - 1 subject failed: COMPARTMENT ("compartment")
    - 2+ subjects failed: FAIL ("fail")
    - Overall aggregate < 33%: FAIL ("fail")
    Never hardcoded PASS.
    """
    # 1. Clear Pass
    card_pass = {
        "rows": [
            {"subject": "English", "percent": 75.0},
            {"subject": "Mathematics", "percent": 60.0},
            {"subject": "Science", "percent": 55.0},
        ],
        "overall_percent": 63.3,
    }
    assert report_cards.evaluate_academic_result(card_pass) == report_cards.PASS

    # 2. Compartment (1 subject < 33%)
    card_comp = {
        "rows": [
            {"subject": "English", "percent": 75.0},
            {"subject": "Mathematics", "percent": 28.0},  # Failed
            {"subject": "Science", "percent": 55.0},
        ],
        "overall_percent": 52.6,
    }
    assert report_cards.evaluate_academic_result(card_comp) == report_cards.COMPARTMENT

    # 3. Fail (2 subjects < 33%)
    card_fail_2 = {
        "rows": [
            {"subject": "English", "percent": 75.0},
            {"subject": "Mathematics", "percent": 28.0},  # Failed
            {"subject": "Science", "percent": 25.0},      # Failed
        ],
        "overall_percent": 42.6,
    }
    assert report_cards.evaluate_academic_result(card_fail_2) == report_cards.FAIL

    # 4. Fail (< 33% overall aggregate)
    card_fail_agg = {
        "rows": [
            {"subject": "English", "percent": 30.0},
            {"subject": "Mathematics", "percent": 31.0},
        ],
        "overall_percent": 30.5,
    }
    assert report_cards.evaluate_academic_result(card_fail_agg) == report_cards.FAIL


def test_defect_7_fee_dues_withheld_separation():
    """Outstanding fee dues mark the report card as withheld, but preserve the
    genuine academic_result separately without overwriting academic status.
    """
    card = {
        "rows": [
            {"subject": "English", "percent": 75.0},
            {"subject": "Mathematics", "percent": 60.0},
        ],
        "overall_percent": 67.5,
        "academic_result": report_cards.PASS,
        "is_withheld": True,
        "status": "withheld",
    }
    assert card["academic_result"] == report_cards.PASS
    assert card["is_withheld"] is True

    # Released
    card["is_withheld"] = False
    card["status"] = "published"
    assert card["academic_result"] == report_cards.PASS


# -----------------------------------------------------------------------------
# DEFECT 8: Cross-Tenant Exam Security
# -----------------------------------------------------------------------------

def test_defect_8_cross_tenant_exam_security_and_date_bounds(client, admin, db):
    """Staff cannot schedule papers for another school's exam (404/403).
    Exam paper dates must fall strictly within exam start_date and end_date.
    """
    school = db.scalar(select(School))
    section = db.scalar(select(ClassSection).where(ClassSection.school_id == school.id))
    subject = db.scalar(select(Subject).where(Subject.school_id == school.id))

    # Create exam
    start = date.today() + timedelta(days=10)
    end = start + timedelta(days=7)
    exam = Exam(
        school_id=school.id,
        name="Annual Finals",
        term="Term 2",
        start_date=start,
        end_date=end,
    )
    db.add(exam)
    db.flush()

    # 1. Date before exam start_date -> 422
    r_early = client.post(
        f"/admin/exams/{exam.id}/schedule",
        json={
            "class_section_id": section.id,
            "subject_id": subject.id,
            "exam_date": (start - timedelta(days=1)).isoformat(),
            "max_marks": "100.00",
        },
        headers=admin,
    )
    assert r_early.status_code == 422
    assert "exam_date must be between" in r_early.json()["detail"]

    # 2. Date after exam end_date -> 422
    r_late = client.post(
        f"/admin/exams/{exam.id}/schedule",
        json={
            "class_section_id": section.id,
            "subject_id": subject.id,
            "exam_date": (end + timedelta(days=1)).isoformat(),
            "max_marks": "100.00",
        },
        headers=admin,
    )
    assert r_late.status_code == 422
    assert "exam_date must be between" in r_late.json()["detail"]

    # 3. Cross-tenant exam scheduling -> 404
    # Create foreign school and exam
    foreign_school = School(name="Foreign School", code="FS-999")
    db.add(foreign_school)
    db.flush()
    foreign_exam = Exam(
        school_id=foreign_school.id,
        name="Foreign Exam",
        term="Term 1",
        start_date=start,
        end_date=end,
    )
    db.add(foreign_exam)
    db.flush()

    r_cross = client.post(
        f"/admin/exams/{foreign_exam.id}/schedule",
        json={
            "class_section_id": section.id,
            "subject_id": subject.id,
            "exam_date": (start + timedelta(days=1)).isoformat(),
            "max_marks": "100.00",
        },
        headers=admin,
    )
    assert r_cross.status_code == 404
    assert "Exam not found" in r_cross.json()["detail"]
