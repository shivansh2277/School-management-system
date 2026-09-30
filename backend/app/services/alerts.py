from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AlertView,
    Attendance,
    AttendanceStatus,
    Enrolment,
    Exam,
    ExamSchedule,
    FeeInvoice,
    Mark,
    ReportCardPublication,
    SchemeComponent,
    Student,
    User,
)
from app.services import attendance, fees, scoping
from app.services.common import current_enrolment


def get_attendance_event_key(
    db: Session, enrolment_id: int | None, att_percent: float
) -> str:
    """Computes a stable event key representing the latest attendance shortage state.
    If a new absence is recorded or absence count increments, the key advances,
    allowing a new alert event to trigger if attendance is still below 75%.
    """
    if enrolment_id:
        latest_absence = db.scalar(
            select(func.max(Attendance.date)).where(
                Attendance.enrolment_id == enrolment_id,
                Attendance.status.in_([AttendanceStatus.absent, AttendanceStatus.half_day]),
            )
        )
        absence_count = (
            db.scalar(
                select(func.count(Attendance.id)).where(
                    Attendance.enrolment_id == enrolment_id,
                    Attendance.status.in_([AttendanceStatus.absent, AttendanceStatus.half_day]),
                )
            )
            or 0
        )
        if latest_absence is not None:
            return f"{latest_absence}_{absence_count}"
    return f"pct_{int(att_percent)}"


def record_alert_view(
    db: Session,
    school_id: int,
    user_id: int,
    student_id: int,
    alert_type: str,
    event_key: str,
) -> bool:
    """Record an alert as viewed by a user for a specific child/student.
    CRITICAL RULE: Fee alerts CANNOT be dismissed by viewing (remain visible until balance is 0).
    """
    if alert_type == "fee":
        return False

    key_str = str(event_key)
    existing = db.scalar(
        select(AlertView.id).where(
            AlertView.user_id == user_id,
            AlertView.student_id == student_id,
            AlertView.alert_type == alert_type,
            AlertView.event_key == key_str,
        )
    )
    if existing is not None:
        return True

    db.add(
        AlertView(
            school_id=school_id,
            user_id=user_id,
            student_id=student_id,
            alert_type=alert_type,
            event_key=key_str,
        )
    )
    db.flush()
    return True


def is_alert_viewed(
    db: Session,
    user_id: int,
    student_id: int,
    alert_type: str,
    event_key: str,
) -> bool:
    """Check whether an alert event has already been viewed by this user for this student.
    Fee alerts always return False (fee alerts are never considered dismissed by view).
    """
    if alert_type == "fee":
        return False

    key_str = str(event_key)
    row = db.scalar(
        select(AlertView.id).where(
            AlertView.user_id == user_id,
            AlertView.student_id == student_id,
            AlertView.alert_type == alert_type,
            AlertView.event_key == key_str,
        )
    )
    return row is not None


def mark_attendance_viewed(
    db: Session, school_id: int, user_id: int, student_id: int
) -> bool:
    """Mark the current attendance shortage alert as viewed for this student."""
    enrolment = current_enrolment(db, student_id)
    att_percent = attendance.student_percent(db, student_id)
    if att_percent is not None and att_percent < 75.0:
        event_key = get_attendance_event_key(
            db, enrolment.id if enrolment else None, att_percent
        )
        return record_alert_view(
            db, school_id, user_id, student_id, "attendance", event_key
        )
    return False


def mark_exam_viewed(
    db: Session, school_id: int, user_id: int, student_id: int, exam_id: int
) -> bool:
    """Mark a specific exam result / report card alert as viewed for this student."""
    exam = db.get(Exam, exam_id)
    if not exam:
        return False
    is_pt = False
    if exam.scheme_component_id:
        sc = db.get(SchemeComponent, exam.scheme_component_id)
        if sc and sc.code == "PT":
            is_pt = True
    elif "Periodic Test" in (exam.name or "") or "PT" in (exam.name or ""):
        is_pt = True

    alert_type = "periodic_test" if is_pt else "report_card"
    return record_alert_view(
        db, school_id, user_id, student_id, alert_type, str(exam_id)
    )


def mark_results_viewed(
    db: Session, school_id: int, user_id: int, student_id: int
) -> None:
    """Mark any currently active report card or periodic test alert as viewed when viewing results."""
    data = get_student_alerts(db, student_id, user_id=None)
    if data.get("latest_report_card"):
        record_alert_view(
            db,
            school_id,
            user_id,
            student_id,
            "report_card",
            str(data["latest_report_card"]["exam_id"]),
        )
    if data.get("latest_periodic_test"):
        record_alert_view(
            db,
            school_id,
            user_id,
            student_id,
            "periodic_test",
            str(data["latest_periodic_test"]["exam_id"]),
        )


def get_student_alerts(
    db: Session, student_id: int, user_id: int | None = None
) -> dict:
    """Evaluate all four important alert types for a given student:
    1. Attendance Shortage (< 75%)
    2. Fee Due (> 0)
    3. Report Card Available
    4. Periodic Test Result Available

    If user_id is provided, filters out alerts that this user has already viewed
    (except Fee Due, which remains visible until balance is 0).
    """
    student = db.get(Student, student_id)
    if student is None:
        return {
            "student_id": student_id,
            "attendance_percent": None,
            "fee_due_amount": 0.0,
            "latest_report_card": None,
            "latest_periodic_test": None,
            "alerts": [],
        }

    enrolment = current_enrolment(db, student_id)

    # 1. Attendance Shortage Alert (< 75.0%)
    att_percent = attendance.student_percent(db, student_id)

    # 2. Fee Due Alert
    fee_due_amount = 0.0
    if enrolment:
        invs = list(db.scalars(select(FeeInvoice).where(FeeInvoice.enrolment_id == enrolment.id)))
        invoice_list = fees.list_invoices(db, invs)
        fee_due_amount = round(
            sum(float(i.get("balance", 0)) for i in invoice_list if float(i.get("balance", 0)) > 0),
            2,
        )

    # 3. Report Card Available Alert
    latest_report_card = None
    if enrolment:
        # Check formal ReportCardPublication first
        pub = db.scalar(
            select(ReportCardPublication)
            .where(ReportCardPublication.enrolment_id == enrolment.id)
            .order_by(ReportCardPublication.published_at.desc())
            .limit(1)
        )
        if pub:
            # Find matching exam if any
            m_exam = db.scalars(
                select(Exam)
                .where(
                    Exam.school_id == student.school_id,
                    Exam.term == pub.term,
                )
                .order_by(Exam.end_date.desc())
                .limit(1)
            ).first()
            latest_report_card = {
                "exam_id": m_exam.id if m_exam else 0,
                "title": f"{pub.term} Report Card",
            }
        else:
            # Check terminal exams where marks exist for this student
            term_exam = db.scalars(
                select(Exam)
                .join(ExamSchedule, ExamSchedule.exam_id == Exam.id)
                .join(Mark, Mark.exam_schedule_id == ExamSchedule.id)
                .outerjoin(SchemeComponent, SchemeComponent.id == Exam.scheme_component_id)
                .where(
                    Mark.student_id == student_id,
                    (SchemeComponent.code.in_(["TERM", "EXAM"]))
                    | (Exam.name.ilike("%Term Examination%"))
                    | (Exam.name.ilike("%Report Card%")),
                )
                .distinct()
                .order_by(Exam.end_date.desc())
                .limit(1)
            ).first()
            if term_exam:
                title = (
                    term_exam.name
                    if "Report Card" in term_exam.name
                    else f"{term_exam.name} Report Card"
                )
                latest_report_card = {
                    "exam_id": term_exam.id,
                    "title": title,
                }

    # 4. Periodic Test Result Alert
    latest_periodic_test = None
    pt_exam = db.scalars(
        select(Exam)
        .join(ExamSchedule, ExamSchedule.exam_id == Exam.id)
        .join(Mark, Mark.exam_schedule_id == ExamSchedule.id)
        .outerjoin(SchemeComponent, SchemeComponent.id == Exam.scheme_component_id)
        .where(
            Mark.student_id == student_id,
            (SchemeComponent.code == "PT")
            | (Exam.name.ilike("%Periodic Test%"))
            | (Exam.name.ilike("%PT%")),
        )
        .distinct()
        .order_by(Exam.end_date.desc())
        .limit(1)
    ).first()
    if pt_exam:
        latest_periodic_test = {
            "exam_id": pt_exam.id,
            "title": pt_exam.name,
        }

    # Build student-facing alerts list
    alerts = []

    # 1. Attendance shortage
    if att_percent is not None and att_percent < 75.0:
        att_event_key = get_attendance_event_key(
            db, enrolment.id if enrolment else None, att_percent
        )
        if not (user_id and is_alert_viewed(db, user_id, student_id, "attendance", att_event_key)):
            alerts.append({
                "id": f"att-{student_id}-{att_event_key}",
                "type": "attendance",
                "title": "Attendance Shortage",
                "message": f"Your attendance is {att_percent}%. Minimum required attendance: 75%.",
                "route": "/(student)/attendance",
                "event_key": att_event_key,
                "severity": "warning",
                "icon": "warning",
            })

    # 2. Fee Due Alert — NEVER dismissed by viewing; only disappears when balance reaches 0
    if fee_due_amount > 0:
        formatted_fee = f"₹{fee_due_amount:,.2f}"
        alerts.append({
            "id": f"fee-{student_id}",
            "type": "fee",
            "title": "Fee Due",
            "message": f"{formatted_fee} outstanding. Please clear dues.",
            "route": None,
            "amount": fee_due_amount,
            "event_key": f"fee-{student_id}",
            "severity": "danger",
            "icon": "cash",
        })

    # 3. Report Card Alert
    if latest_report_card:
        rc_event_key = str(latest_report_card["exam_id"])
        if not (user_id and is_alert_viewed(db, user_id, student_id, "report_card", rc_event_key)):
            alerts.append({
                "id": f"rc-{student_id}-{rc_event_key}",
                "type": "report_card",
                "title": "Report Card Available",
                "message": f"{latest_report_card['title']} is now available. View Report Card →",
                "route": "/(student)/results",
                "exam_id": latest_report_card["exam_id"],
                "event_key": rc_event_key,
                "severity": "info",
                "icon": "document-text",
            })

    # 4. Periodic Test Alert
    if latest_periodic_test:
        pt_event_key = str(latest_periodic_test["exam_id"])
        if not (user_id and is_alert_viewed(db, user_id, student_id, "periodic_test", pt_event_key)):
            alerts.append({
                "id": f"pt-{student_id}-{pt_event_key}",
                "type": "periodic_test",
                "title": "Periodic Test Result Available",
                "message": f"{latest_periodic_test['title']} results are now available. View Results →",
                "route": "/(student)/results",
                "exam_id": latest_periodic_test["exam_id"],
                "event_key": pt_event_key,
                "severity": "info",
                "icon": "bar-chart",
            })

    return {
        "student_id": student_id,
        "attendance_percent": att_percent,
        "fee_due_amount": fee_due_amount,
        "latest_report_card": latest_report_card,
        "latest_periodic_test": latest_periodic_test,
        "alerts": alerts,
    }


def get_parent_alerts(db: Session, parent_user: User) -> list[dict]:
    """Collect and format all active alerts across all of a parent's children.
    Each alert carries clear child attribution and switches context on tap.
    Viewed states are tracked per child and per alert independently.
    """
    child_ids = scoping.child_ids_for(db, parent_user)
    all_alerts = []

    for cid in child_ids:
        st = db.get(Student, cid)
        if not st:
            continue
        child_name = st.user.full_name
        # Evaluates alerts for child `cid`, filtering out alerts already viewed by `parent_user`
        data = get_student_alerts(db, cid, user_id=parent_user.id)

        for alert in data["alerts"]:
            parent_alert = dict(alert)
            parent_alert["child_id"] = cid
            parent_alert["child_name"] = child_name
            parent_alert["title"] = f"{alert['title']} — {child_name}"

            if alert["type"] == "attendance":
                parent_alert["route"] = "/(parent)/attendance"
                parent_alert["message"] = f"Attendance: {data['attendance_percent']}%. Minimum required: 75%."
            elif alert["type"] == "fee":
                parent_alert["route"] = "/(parent)/fees"
                parent_alert["message"] = f"₹{data['fee_due_amount']:,.2f} outstanding. View Fees →"
            elif alert["type"] in ("report_card", "periodic_test"):
                parent_alert["route"] = "/(parent)/results"

            all_alerts.append(parent_alert)

    return all_alerts
