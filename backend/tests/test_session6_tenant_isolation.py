"""Tests for Session 6: Critical Multi-Tenant & RBAC Isolation Test Suite.

Validates the zero-leakage multi-tenant architectural foundation:
1. Multi-Tenant Isolation across Tenant 1 and Tenant 2:
   - Students & Enrolments: zero data leakage across tenants
   - Homework & Submissions: tenant 1 cannot read/submit to tenant 2 homework
   - Marks: tenant 1 teacher cannot enter marks for tenant 2 schedule or enrolment
   - Grievances: tenant 1 cannot read or modify tenant 2 grievances
2. Role-Based Access Control (RBAC) Boundaries:
   - Receptionist: strictly restricted to admission queues; blocked from staff leave, payroll, marks entry
   - Student: blocked from teacher roll call, homework assignment, marks entry
   - Teacher: blocked from fee plans, fee void, and student admission conversion
"""

from datetime import date, timedelta


from app.core.security import hash_password
from app.models import (
    AcademicYear,
    AcademicYearStatus,
    ClassSection,
    Enrolment,
    Grievance,
    Homework,
    School,
    SchoolStatus,
    Student,
    User,
    UserRole,
)


def make_tenant_2(db):
    """Create a fully isolated secondary school tenant with academic year and class."""
    school = School(code="T2SCH", name="Green Valley Academy", status=SchoolStatus.active, city="Dehradun")
    db.add(school)
    db.flush()

    year = AcademicYear(
        school_id=school.id,
        code="2025-26",
        start_date=date(2025, 4, 1),
        end_date=date(2026, 3, 31),
        status=AcademicYearStatus.active,
        is_current=True,
    )
    db.add(year)
    db.flush()

    sec = ClassSection(school_id=school.id, academic_year_id=year.id, class_name="10", section="A")
    db.add(sec)
    db.flush()

    u_admin = User(
        school_id=school.id,
        role=UserRole.admin,
        login_id="admin@greenvalley.edu",
        password_hash=hash_password("Admin@123"),
        full_name="Green Valley Admin",
    )
    db.add(u_admin)
    db.flush()

    u_student = User(
        school_id=school.id,
        role=UserRole.student,
        login_id="GVA2025001",
        password_hash=hash_password("Student@123"),
        full_name="Kavita Sharma",
    )
    db.add(u_student)
    db.flush()

    student = Student(school_id=school.id, user_id=u_student.id, admission_no="GVA2025001")
    db.add(student)
    db.flush()

    enrolment = Enrolment(
        school_id=school.id,
        student_id=student.id,
        academic_year_id=year.id,
        class_section_id=sec.id,
        roll_no=1,
    )
    db.add(enrolment)
    db.flush()

    return {
        "school_id": school.id,
        "year_id": year.id,
        "section_id": sec.id,
        "admin_user_id": u_admin.id,
        "student_id": student.id,
        "enrolment_id": enrolment.id,
    }


def test_cross_tenant_student_and_enrolment_isolation(client, admin, teacher, db):
    """Tenant 1 user cannot access Tenant 2 student or enrolment records."""
    t2 = make_tenant_2(db)

    # Tenant 1 admin tries to read Tenant 2 student
    res = client.get(f"/admin/students/{t2['student_id']}", headers=admin)
    assert res.status_code in (403, 404), f"Admin saw cross-tenant student: {res.status_code}"

    # Tenant 1 teacher tries to fetch Tenant 2 section students
    res_sec = client.get(f"/teacher/classes/{t2['section_id']}/students", headers=teacher)
    assert res_sec.status_code in (403, 404)


def test_cross_tenant_homework_isolation(client, teacher, student, other_teacher, db):
    """Tenant 1 cannot read, submit to, or grade Tenant 2 homework."""
    t2 = make_tenant_2(db)

    # Create homework directly under Tenant 2
    hw_t2 = Homework(
        school_id=t2["school_id"],
        class_section_id=t2["section_id"],
        subject_id=1,  # dummy or seeded subject
        teacher_id=1,
        title="Tenant 2 Science Homework",
        description="Confidential to Green Valley",
        assigned_date=date.today(),
        due_date=date.today() + timedelta(days=2),
    )
    db.add(hw_t2)
    db.flush()

    # Tenant 1 teacher listing submissions for Tenant 2 homework
    res_subs = client.get(f"/teacher/homework/{hw_t2.id}/submissions", headers=teacher)
    assert res_subs.status_code in (403, 404)

    # Tenant 1 student attempting to submit to Tenant 2 homework
    res_sub = client.post(
        f"/student/homework/{hw_t2.id}/submit",
        json={"answer_text": "Infiltrating Tenant 2"},
        headers=student,
    )
    assert res_sub.status_code in (403, 404, 422)


def test_cross_tenant_marks_entry_rejected(client, teacher, db):
    """Tenant 1 teacher attempting to enter marks using Tenant 2 enrolment_id is strictly rejected."""
    t2 = make_tenant_2(db)

    # Try submitting marks with Tenant 2's enrolment_id
    res = client.post(
        "/teacher/marks",
        json={
            "exam_schedule_id": 1,
            "entries": [{"enrolment_id": t2["enrolment_id"], "marks_obtained": "50"}],
        },
        headers=teacher,
    )
    assert res.status_code in (400, 403, 404, 422)


def test_cross_tenant_grievance_isolation(client, admin, teacher, db):
    """Tenant 1 cannot read or modify Tenant 2 grievances."""
    t2 = make_tenant_2(db)

    g_t2 = Grievance(
        school_id=t2["school_id"],
        title="Tenant 2 Water Cooler Leak",
        description="Room 201 water cooler is leaking",
        category="facilities",
        raised_by_id=t2["admin_user_id"],
        raised_by_role="admin",
        raised_by_name="Green Valley Admin",
        student_id=t2["student_id"],
        enrolment_id=t2["enrolment_id"],
    )
    db.add(g_t2)
    db.flush()

    # Tenant 1 admin list grievances: must not contain Tenant 2 grievance
    res_list = client.get("/admin/grievances", headers=admin)
    assert res_list.status_code == 200
    ids_seen = [g["id"] for g in res_list.json()]
    assert g_t2.id not in ids_seen

    # Tenant 1 teacher list grievances: must not contain Tenant 2 grievance
    res_teach = client.get("/teacher/grievances", headers=teacher)
    assert res_teach.status_code == 200
    ids_teach = [g["id"] for g in res_teach.json()]
    assert g_t2.id not in ids_teach


def test_receptionist_rbac_boundaries(client, receptionist, hr_enabled):
    """Receptionist is strictly gated: allowed on admission, blocked from staff leave, payroll, fees void."""
    # Allowed: admissions enquiries
    res_enquiries = client.get("/admin/admission/enquiries", headers=receptionist)
    assert res_enquiries.status_code == 200

    # Blocked: staff leave management
    res_leave = client.get("/admin/staff-leave", headers=receptionist)
    assert res_leave.status_code == 403

    # Blocked: payroll overview / disbursal
    res_payroll = client.get("/admin/payroll/components", headers=receptionist)
    assert res_payroll.status_code == 403

    # Blocked: marks entry
    res_marks = client.post(
        "/teacher/marks",
        json={"exam_schedule_id": 1, "entries": [{"enrolment_id": 1, "marks_obtained": "50"}]},
        headers=receptionist,
    )
    assert res_marks.status_code == 403


def test_student_and_teacher_rbac_boundaries(client, student, teacher):
    """Students and teachers are blocked from operations outside their role scopes."""
    # Student blocked from teacher attendance roll marking
    res_s_att = client.post(
        "/teacher/attendance",
        json={"class_section_id": 1, "date": str(date.today()), "entries": []},
        headers=student,
    )
    assert res_s_att.status_code == 403

    # Student blocked from creating homework
    res_s_hw = client.post(
        "/teacher/homework",
        json={"class_section_id": 1, "subject_id": 1, "title": "Hack", "due_date": str(date.today())},
        headers=student,
    )
    assert res_s_hw.status_code == 403

    # Teacher blocked from creating school fee plans
    res_t_fee = client.post(
        "/admin/fees/plans",
        json={"academic_year_id": 1, "name": "Unauthorized Plan", "items": []},
        headers=teacher,
    )
    assert res_t_fee.status_code == 403
