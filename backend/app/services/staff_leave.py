"""Staff leave: applying, approving, and what approval does to the timetable.

§5.3.9 names the failure this module exists to prevent, and calls it the single
most common real-world HR/timetable failure: **approving a teacher's leave that
silently leaves classes unattended.** Approval here therefore does not merely
set a status. It walks the teacher's timetable across the dates, and raises a
`pending` substitution for every period they were due to teach — so the class
appears on the arrangements queue as uncovered rather than being discovered
empty on the morning.

That reuses Part 3's `substitutions` table exactly as it stands: a row per date,
null substitute while nobody has been found, and §5.7.10's "unfilled" report
already counts them.

Two smaller rules, both §5.3.9:

- **Overlapping requests for one employee are rejected.** Two approved leaves
  covering the same Tuesday would each debit the balance for it.
- **Leave beyond the balance needs an explicit exception**, recorded on the
  request rather than inferred from the numbers not adding up.
"""

from datetime import UTC, date as Date, datetime, time as Time, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    ClassSection,
    ClassSubjectTeacher,
    DayOfWeek,
    Employee,
    EmployeeStatus,
    LeaveBalance,
    LeaveStatus,
    LeaveTypeDef,
    StaffLeaveRequest,
    Subject,
    Substitution,
    SubstitutionStatus,
    TimetableSlot,
    User,
)
from app.services import attendance as att
from app.services import audit
from app.services.notifications import notify_user
from app.services.timetable import DAY_BY_WEEKDAY

# A decision has been made; the request is no longer a claim on the balance.
CLOSED = (LeaveStatus.rejected, LeaveStatus.cancelled)
# Statuses that still hold days against the employee, for the overlap check.
LIVE = (LeaveStatus.applied, LeaveStatus.approved)


def _bad(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


# --- leave types and balances ----------------------------------------------


def create_type(
    db: Session,
    school_id: int,
    *,
    code: str,
    name: str,
    annual_quota: Decimal,
    is_paid: bool = True,
) -> LeaveTypeDef:
    if annual_quota < 0:
        raise _bad("A leave type cannot have a negative quota")
    row = LeaveTypeDef(
        school_id=school_id,
        code=code.strip().upper(),
        name=name.strip(),
        annual_quota=Decimal(str(annual_quota)),
        is_paid=is_paid,
    )
    db.add(row)
    db.flush()
    return row


def types_for(db: Session, school_id: int) -> list[LeaveTypeDef]:
    return list(
        db.scalars(
            select(LeaveTypeDef)
            .where(LeaveTypeDef.school_id == school_id, LeaveTypeDef.active.is_(True))
            .order_by(LeaveTypeDef.code)
        )
    )


def balance(
    db: Session, employee: Employee, leave_type: LeaveTypeDef, academic_year_id: int
) -> LeaveBalance:
    """This employee's balance of this type, opened at the quota if absent.

    Opening it lazily rather than pre-creating one per employee per type per
    year means a new leave type does not need a backfill, and an employee who
    never takes casual leave carries no row.

    **Unused leave does not carry forward** (owner, 7 September 2026). The
    balance is keyed to the academic year and opens at the year's quota, so a
    new year starts fresh however much went untaken — there is deliberately no
    path that adds last year's remainder. A later session that "helpfully"
    carries a balance over is changing a decision, not fixing an omission;
    `test_unused_leave_does_not_carry_forward` fails if it does.
    """
    row = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.academic_year_id == academic_year_id,
        )
    )
    if row is None:
        row = LeaveBalance(
            school_id=employee.school_id,
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            academic_year_id=academic_year_id,
            entitled=leave_type.annual_quota,
            used=Decimal(0),
        )
        db.add(row)
        db.flush()
    return row


def balances_for(
    db: Session, employee: Employee, academic_year_id: int
) -> list[LeaveBalance]:
    return [
        balance(db, employee, t, academic_year_id)
        for t in types_for(db, employee.school_id)
    ]


# --- applying ---------------------------------------------------------------


def _days(
    db: Session, school_id: int, start: Date, end: Date, half_day: bool
) -> Decimal:
    """Working days in the range, from the same calendar attendance uses.

    A Sunday or a declared holiday is not leave — charging somebody a casual
    day for a Sunday is the kind of arithmetic staff notice immediately.
    """
    count = att.working_days(db, school_id, start, end)
    if half_day:
        if start != end:
            raise _bad("A half day covers one date")
        return Decimal("0.5") if count else Decimal(0)
    return Decimal(count)


def overlapping(
    db: Session, employee: Employee, start: Date, end: Date, exclude_id: int | None = None
) -> StaffLeaveRequest | None:
    q = select(StaffLeaveRequest).where(
        StaffLeaveRequest.employee_id == employee.id,
        StaffLeaveRequest.status.in_(LIVE),
        StaffLeaveRequest.from_date <= end,
        StaffLeaveRequest.to_date >= start,
    )
    if exclude_id is not None:
        q = q.where(StaffLeaveRequest.id != exclude_id)
    return db.scalar(q)


def apply_for(
    db: Session,
    employee: Employee,
    *,
    leave_type_id: int,
    academic_year_id: int,
    from_date: Date,
    to_date: Date,
    reason: str,
    is_half_day: bool = False,
) -> StaffLeaveRequest:
    if to_date < from_date:
        raise _bad("The last day cannot precede the first")
    if not employee.in_service:
        raise _bad(f"{employee.user.full_name} is no longer in service")

    leave_type = db.get(LeaveTypeDef, leave_type_id)
    if leave_type is None or leave_type.school_id != employee.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leave type not found")

    clash = overlapping(db, employee, from_date, to_date)
    if clash is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This overlaps an existing request from {clash.from_date} to "
            f"{clash.to_date}",
        )

    days = _days(db, employee.school_id, from_date, to_date, is_half_day)
    if days <= 0:
        raise _bad(
            "Those dates contain no working days — the school is closed "
            "throughout"
        )

    row = StaffLeaveRequest(
        school_id=employee.school_id,
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        academic_year_id=academic_year_id,
        from_date=from_date,
        to_date=to_date,
        is_half_day=is_half_day,
        days=days,
        reason=reason,
        status=LeaveStatus.applied,
    )
    db.add(row)
    db.flush()
    return row


# --- what a teacher was due to teach ---------------------------------------


def dates_in(start: Date, end: Date) -> list[Date]:
    return [start + timedelta(days=n) for n in range((end - start).days + 1)]


def affected_periods(
    db: Session, request: StaffLeaveRequest
) -> list[tuple[Date, TimetableSlot]]:
    """Every lesson this teacher would have taught across the leave.

    Empty for a non-teaching employee, which is correct rather than a special
    case: the accountant's leave leaves no class unattended.
    """
    slots = list(
        db.scalars(
            select(TimetableSlot).where(
                TimetableSlot.teacher_id == request.employee_id
            )
        )
    )
    if not slots:
        return []
    by_day: dict[DayOfWeek, list[TimetableSlot]] = {}
    for slot in slots:
        by_day.setdefault(slot.day_of_week, []).append(slot)

    holidays = att.holidays_between(
        db, request.school_id, request.from_date, request.to_date
    )
    out = []
    for day in dates_in(request.from_date, request.to_date):
        if not att.is_working_day(day, holidays):
            continue
        for slot in by_day.get(DAY_BY_WEEKDAY.get(day.weekday()), []):
            out.append((day, slot))
    return out


def on_leave(db: Session, employee_id: int, on: Date) -> StaffLeaveRequest | None:
    """Is this member of staff on approved leave that day?

    The question `timetable.arrange()` could not ask before this module existed,
    and the reason a substitute could be assigned to cover a lesson on a day
    they were themselves away.
    """
    return db.scalar(
        select(StaffLeaveRequest).where(
            StaffLeaveRequest.employee_id == employee_id,
            StaffLeaveRequest.status == LeaveStatus.approved,
            StaffLeaveRequest.from_date <= on,
            StaffLeaveRequest.to_date >= on,
        )
    )


# --- deciding ---------------------------------------------------------------


def approve(
    db: Session,
    user: User,
    request: StaffLeaveRequest,
    *,
    note: str | None = None,
    allow_exception: bool = False,
) -> dict:
    """Approve, debit the balance, and raise cover for every affected lesson.

    Returns the request with the substitutions it created, because §5.3.9 wants
    approval to *surface* the affected periods rather than leave them to be
    discovered. An unfilled row is the honest state and §5.7.10 already counts
    it; what must not happen is no row at all.
    """
    if request.status is not LeaveStatus.applied:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This request is already {request.status.value}",
        )

    employee = db.get(Employee, request.employee_id)
    bal = balance(db, employee, request.leave_type, request.academic_year_id)
    if request.days > bal.remaining and not allow_exception:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{employee.user.full_name} has {bal.remaining} day(s) of "
            f"{request.leave_type.name} left and this request is "
            f"{request.days}. Approving it anyway is an explicit exception.",
        )

    request.balance_exception = request.days > bal.remaining
    bal.used = bal.used + request.days
    request.status = LeaveStatus.approved
    request.decided_by = user.id
    request.decided_at = datetime.now(UTC)
    request.decision_note = note

    # Approving leave writes the register, exactly as student leave does. Any
    # other arrangement leaves "approved leave" in one table and `absent` in
    # another, reconciled only by whoever remembers.
    from app.services import staff_attendance

    register = staff_attendance.write_leave(db, request)

    created = []
    for day, slot in affected_periods(db, request):
        existing = db.scalar(
            select(Substitution).where(
                Substitution.timetable_slot_id == slot.id, Substitution.date == day
            )
        )
        if existing is not None:
            continue
        cover = Substitution(
            school_id=request.school_id,
            timetable_slot_id=slot.id,
            date=day,
            absent_teacher_id=request.employee_id,
            substitute_teacher_id=None,
            reason=f"{request.leave_type.name} approved for "
            f"{employee.user.full_name}",
            status=SubstitutionStatus.pending,
        )
        db.add(cover)
        created.append(cover)
    db.flush()

    audit.record(
        db,
        actor=user,
        school_id=request.school_id,
        entity_type="staff_leave_request",
        entity_id=request.id,
        action=AuditAction.status_change,
        before={"status": LeaveStatus.applied.value},
        after={
            "status": LeaveStatus.approved.value,
            "days": str(request.days),
            "balance_exception": request.balance_exception,
            "substitutions_raised": len(created),
            "register_days_written": len(register),
        },
        reason=note or "Leave approved",
        academic_year_id=request.academic_year_id,
    )
    return {
        "request": request,
        "substitutions": created,
        "register_days": register,
    }


def reject(
    db: Session, user: User, request: StaffLeaveRequest, *, reason: str
) -> StaffLeaveRequest:
    if request.status is not LeaveStatus.applied:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This request is already {request.status.value}",
        )
    # Purge any provisional substitutions arranged for this request
    db.execute(
        Substitution.__table__.delete().where(
            Substitution.leave_request_id == request.id
        )
    )
    request.status = LeaveStatus.rejected
    request.decided_by = user.id
    request.decided_at = datetime.now(UTC)
    request.decision_note = reason
    audit.record(
        db,
        actor=user,
        school_id=request.school_id,
        entity_type="staff_leave_request",
        entity_id=request.id,
        action=AuditAction.status_change,
        before={"status": LeaveStatus.applied.value},
        after={"status": LeaveStatus.rejected.value},
        reason=reason,
        academic_year_id=request.academic_year_id,
    )
    db.flush()
    return request


def cancel(
    db: Session, user: User, request: StaffLeaveRequest, *, reason: str
) -> StaffLeaveRequest:
    """Withdraw a request, crediting the balance back if it was approved.

    The substitutions raised for it are dropped only where nobody has been
    found yet: a colleague who already agreed to cover has been told, and
    deleting the row would be the system forgetting a conversation that
    happened.
    """
    if request.status in CLOSED:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This request is already {request.status.value}",
        )
    if request.status is LeaveStatus.approved:
        employee = db.get(Employee, request.employee_id)
        bal = balance(db, employee, request.leave_type, request.academic_year_id)
        bal.used = max(Decimal(0), bal.used - request.days)
        # The register rows this leave wrote go with it; a day somebody was
        # actually marked present on is left alone, because `write_leave` never
        # touched it.
        from app.models import AttendanceStatus, StaffAttendance

        for row in db.scalars(
            select(StaffAttendance).where(
                StaffAttendance.employee_id == request.employee_id,
                StaffAttendance.date >= request.from_date,
                StaffAttendance.date <= request.to_date,
                StaffAttendance.status == AttendanceStatus.leave,
                StaffAttendance.marked_by.is_(None),
            )
        ):
            db.delete(row)
        for cover in db.scalars(
            select(Substitution).where(
                Substitution.absent_teacher_id == request.employee_id,
                Substitution.date >= request.from_date,
                Substitution.date <= request.to_date,
                Substitution.substitute_teacher_id.is_(None),
            )
        ):
            db.delete(cover)

    request.status = LeaveStatus.cancelled
    request.decided_by = user.id
    request.decided_at = datetime.now(UTC)
    request.decision_note = reason
    audit.record(
        db,
        actor=user,
        school_id=request.school_id,
        entity_type="staff_leave_request",
        entity_id=request.id,
        action=AuditAction.status_change,
        before={"status": LeaveStatus.approved.value},
        after={"status": LeaveStatus.cancelled.value},
        reason=reason,
        academic_year_id=request.academic_year_id,
    )
    db.flush()
    return request


def to_out(db: Session, row: StaffLeaveRequest) -> dict:
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "employee": row.employee.user.full_name if row.employee and row.employee.user else "",
        "employee_name": row.employee.user.full_name if row.employee and row.employee.user else "",
        "employee_code": row.employee.employee_code if row.employee else "",
        "leave_type": row.leave_type.code if row.leave_type else None,
        "leave_type_name": row.leave_type.name if row.leave_type else "Teacher Leave",
        "from_date": row.from_date,
        "to_date": row.to_date,
        "is_half_day": row.is_half_day,
        "days": row.days,
        "reason": row.reason,
        "status": row.status,
        "balance_exception": row.balance_exception,
        "decided_at": row.decided_at,
        "decision_note": row.decision_note,
    }


def used_from_requests(
    db: Session, employee_id: int, leave_type_id: int, academic_year_id: int
) -> Decimal:
    """What the approved requests add up to.

    `LeaveBalance.used` is maintained incrementally because it is read on every
    application; this is the same number derived the slow way, and a test holds
    the two together.
    """
    total = db.scalar(
        select(func.sum(StaffLeaveRequest.days)).where(
            StaffLeaveRequest.employee_id == employee_id,
            StaffLeaveRequest.leave_type_id == leave_type_id,
            StaffLeaveRequest.academic_year_id == academic_year_id,
            StaffLeaveRequest.status == LeaveStatus.approved,
        )
    )
    return Decimal(total or 0)


# --- Teacher Leave Management (Mobile App & Timetable Substitution Gate) ---


def is_casual_leave(leave_type: LeaveTypeDef | None) -> bool:
    if leave_type is None:
        return False
    code = (leave_type.code or "").strip().upper()
    name = (leave_type.name or "").lower()
    return code == "CL" or "casual" in name


def ranked_substitutes_for_slot(
    db: Session, school_id: int, slot: TimetableSlot, on_date: Date, absent_teacher_id: int
) -> list[dict]:
    """Computes available substitute teachers for a slot on a given date, ranked by:
    1. Same subject & grade/class
    2. Same subject (other classes)
    3. Same grade/class (other subjects)
    4. Other eligible, available teachers
    """
    # 1. Teachers busy teaching in that period on that day of week
    busy_teaching = set(
        db.scalars(
            select(TimetableSlot.teacher_id).where(
                TimetableSlot.school_id == school_id,
                TimetableSlot.day_of_week == slot.day_of_week,
                TimetableSlot.period_id == slot.period_id,
            )
        )
    )

    # 2. Teachers busy substituting in that period on on_date (not rejected)
    busy_substituting = set(
        db.scalars(
            select(Substitution.substitute_teacher_id)
            .join(TimetableSlot, TimetableSlot.id == Substitution.timetable_slot_id)
            .where(
                Substitution.date == on_date,
                TimetableSlot.period_id == slot.period_id,
                Substitution.substitute_teacher_id.is_not(None),
                Substitution.status.in_((
                    SubstitutionStatus.pending,
                    SubstitutionStatus.provisional,
                    SubstitutionStatus.assigned,
                    SubstitutionStatus.completed,
                )),
            )
        )
    )

    # 3. All active employees in service for this school (excluding absent teacher)
    all_teachers = list(
        db.scalars(
            select(Employee).where(
                Employee.school_id == school_id,
                Employee.status == EmployeeStatus.active,
                Employee.exited_on.is_(None),
                Employee.id != absent_teacher_id,
            )
        )
    )

    # Filter available: not busy teaching, not busy substituting, not on approved leave, and app access not blocked
    available: list[Employee] = []
    for emp in all_teachers:
        if emp.id in busy_teaching:
            continue
        if emp.id in busy_substituting:
            continue
        if on_leave(db, emp.id, on_date) is not None:
            continue
        if emp.user and emp.user.app_access_blocked:
            continue
        available.append(emp)

    if not available:
        return []

    available_ids = [e.id for e in available]

    cst_rows = list(
        db.execute(
            select(
                ClassSubjectTeacher.teacher_id,
                ClassSubjectTeacher.subject_id,
                ClassSubjectTeacher.class_section_id,
                ClassSection.class_name,
            )
            .join(ClassSection, ClassSection.id == ClassSubjectTeacher.class_section_id)
            .where(ClassSubjectTeacher.teacher_id.in_(available_ids))
        ).all()
    )

    cst_by_teacher: dict[int, list[tuple[int, int, str]]] = {}
    for teacher_id, subject_id, class_section_id, class_name in cst_rows:
        cst_by_teacher.setdefault(teacher_id, []).append((subject_id, class_section_id, class_name))

    slot_class_name = slot.class_section.class_name if slot.class_section else None
    slot_subject_id = slot.subject_id

    ranked = []
    for emp in available:
        assignments = cst_by_teacher.get(emp.id, [])
        # Each item is (sub_id, sec_id, cls_name)
        same_subject_and_grade = any(
            sub_id == slot_subject_id
            and (sec_id == slot.class_section_id or (slot_class_name and cls_name == slot_class_name))
            for sub_id, sec_id, cls_name in assignments
        )
        same_subject = any(sub_id == slot_subject_id for sub_id, sec_id, cls_name in assignments)
        same_grade = any(
            sec_id == slot.class_section_id or (slot_class_name and cls_name == slot_class_name)
            for sub_id, sec_id, cls_name in assignments
        )

        subject_name = slot.subject.name if slot.subject else "Subject"
        grade_name = slot_class_name or (slot.class_section.label if slot.class_section else "Grade")

        if same_subject_and_grade:
            rank = 1
            rank_label = "Same Subject & Grade"
            reason_str = f"Teaches {subject_name} in Class {grade_name}"
        elif same_subject:
            rank = 2
            rank_label = "Same Subject"
            reason_str = f"Teaches {subject_name}"
        elif same_grade:
            rank = 3
            rank_label = "Same Grade"
            reason_str = f"Teaches other subjects in Class {grade_name}"
        else:
            rank = 4
            rank_label = "Available Teacher"
            reason_str = "Free in this period"

        emp_name = emp.user.full_name if emp.user else f"Employee {emp.id}"
        ranked.append({
            "teacher_id": emp.id,
            "teacher_name": emp_name,
            "employee_code": emp.employee_code or "",
            "rank": rank,
            "rank_label": rank_label,
            "reason": reason_str,
        })

    ranked.sort(key=lambda r: (r["rank"], r["teacher_name"]))
    return ranked


def inspect_affected_periods(
    db: Session,
    employee: Employee,
    *,
    from_date: Date,
    to_date: Date,
    is_half_day: bool = False,
    half_day_period: str | None = None,
) -> dict:
    """Walks the teacher's timetable across dates and returns every period affected
    along with ranked substitute recommendations.
    """
    if to_date < from_date:
        raise _bad("The last day cannot precede the first")

    holidays = att.holidays_between(db, employee.school_id, from_date, to_date)
    working_dates = [
        d for d in dates_in(from_date, to_date)
        if att.is_working_day(d, holidays)
    ]

    slots = list(
        db.scalars(
            select(TimetableSlot)
            .where(TimetableSlot.teacher_id == employee.id)
            .order_by(TimetableSlot.period_id)
        )
    )

    by_day: dict[DayOfWeek, list[TimetableSlot]] = {}
    for slot in slots:
        by_day.setdefault(slot.day_of_week, []).append(slot)

    periods_out = []
    for day in working_dates:
        dow = DAY_BY_WEEKDAY.get(day.weekday())
        day_slots = by_day.get(dow, [])
        for slot in day_slots:
            if is_half_day and half_day_period:
                if half_day_period.lower() == "morning" and slot.period.start_time.hour >= 13:
                    continue
                if half_day_period.lower() == "afternoon" and slot.period.start_time.hour < 12:
                    continue

            ranked = ranked_substitutes_for_slot(db, employee.school_id, slot, day, employee.id)
            periods_out.append({
                "date": str(day),
                "slot_id": slot.id,
                "period_id": slot.period_id,
                "period_no": slot.period.period_no,
                "start_time": f"{slot.period.start_time:%H:%M}",
                "end_time": f"{slot.period.end_time:%H:%M}",
                "time": f"{slot.period.start_time:%H:%M} - {slot.period.end_time:%H:%M}",
                "class_section_id": slot.class_section_id,
                "class_label": slot.class_section.label if slot.class_section else "",
                "subject_id": slot.subject_id,
                "subject_name": slot.subject.name if slot.subject else "",
                "room": slot.room,
                "ranked_substitutes": ranked,
            })

    return {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "is_half_day": is_half_day,
        "half_day_period": half_day_period,
        "total_periods": len(periods_out),
        "periods": periods_out,
    }


def apply_teacher_leave(
    db: Session,
    employee: Employee,
    *,
    from_date: Date,
    to_date: Date,
    reason: str,
    is_half_day: bool = False,
    half_day_period: str | None = None,
    leave_type_id: int | None = None,
    substitutions: list[dict] | None = None,
) -> StaffLeaveRequest:
    """Teacher applies for personal leave from the mobile app.

    If leave type is Casual Leave (CL):
      - 100% of affected periods across dates must have proposed substitutes.
      - Proposed substitutes receive notifications and can Accept / Reject.
    If non-casual leave (SL, EL, etc.):
      - Submitted directly without substitutions.
    """
    if to_date < from_date:
        raise _bad("The last day cannot precede the first")
    if not employee.in_service:
        raise _bad(f"{employee.user.full_name} is no longer in service")
    if not reason or not reason.strip():
        raise _bad("A reason for leave is required")

    clash = overlapping(db, employee, from_date, to_date)
    if clash is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This overlaps an existing leave request from {clash.from_date} to {clash.to_date}",
        )

    days = _days(db, employee.school_id, from_date, to_date, is_half_day)
    if days <= 0:
        raise _bad(
            "Those dates contain no working days — the school is closed throughout"
        )

    from app.services import tenancy

    year = tenancy.current_year(db, employee.school_id)
    if year is None:
        raise _bad("No active academic year configured")

    leave_type: LeaveTypeDef | None = None
    if leave_type_id is not None:
        leave_type = db.get(LeaveTypeDef, leave_type_id)
        if leave_type is None or leave_type.school_id != employee.school_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Leave type not found")

    is_cl = is_casual_leave(leave_type)
    sub_inputs = substitutions or []
    periods = []
    sub_dict: dict[tuple[str, int], int] = {}

    if is_cl:
        # Check affected periods
        inspected = inspect_affected_periods(
            db,
            employee,
            from_date=from_date,
            to_date=to_date,
            is_half_day=is_half_day,
            half_day_period=half_day_period,
        )
        periods = inspected["periods"]
        if periods:
            sub_dict = {
                (str(s.get("date")), int(s.get("slot_id"))): int(s.get("substitute_teacher_id"))
                for s in sub_inputs
                if s.get("substitute_teacher_id") is not None
            }
            missing = [p for p in periods if (p["date"], p["slot_id"]) not in sub_dict]
            if missing:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Casual Leave requires a substitute for every affected period. Missing {len(missing)} period(s).",
                )

            for p in periods:
                sub_id = sub_dict[(p["date"], p["slot_id"])]
                sub_emp = db.get(Employee, sub_id)
                if sub_emp is None or sub_emp.school_id != employee.school_id:
                    raise HTTPException(status.HTTP_404_NOT_FOUND, f"Substitute teacher {sub_id} not found")
                if sub_emp.id == employee.id:
                    raise _bad("The absent teacher cannot substitute for themselves")

    row = StaffLeaveRequest(
        school_id=employee.school_id,
        employee_id=employee.id,
        leave_type_id=leave_type.id if leave_type else None,
        academic_year_id=year.id,
        from_date=from_date,
        to_date=to_date,
        is_half_day=is_half_day,
        days=days,
        reason=reason.strip(),
        status=LeaveStatus.applied,
    )
    db.add(row)
    db.flush()

    if is_cl and periods:
        for p in periods:
            sub_id = sub_dict[(p["date"], p["slot_id"])]
            sub_emp = db.get(Employee, sub_id)
            sub_row = Substitution(
                school_id=employee.school_id,
                timetable_slot_id=p["slot_id"],
                date=Date.fromisoformat(p["date"]),
                absent_teacher_id=employee.id,
                substitute_teacher_id=sub_emp.id,
                leave_request_id=row.id,
                reason=f"Cover for {employee.user.full_name} ({leave_type.name if leave_type else 'Casual Leave'})",
                status=SubstitutionStatus.pending,
            )
            db.add(sub_row)
            if sub_emp.user_id:
                notify_user(
                    db,
                    school_id=employee.school_id,
                    user_id=sub_emp.user_id,
                    title="Substitution Request",
                    message=(
                        f"{employee.user.full_name} has requested you to cover {p['class_label']} "
                        f"(Period {p['period_no']}, {p['time']}) on {p['date']}."
                    ),
                    category="substitution_request",
                )
    elif sub_inputs:
        # Non-casual leave, but substitutions were provided
        for s in sub_inputs:
            sub_id = s.get("substitute_teacher_id")
            if not sub_id:
                continue
            sub_emp = db.get(Employee, int(sub_id))
            if not sub_emp or sub_emp.school_id != employee.school_id:
                continue
            sub_date = Date.fromisoformat(str(s["date"])) if isinstance(s["date"], str) else s["date"]
            sub_row = Substitution(
                school_id=employee.school_id,
                timetable_slot_id=int(s["slot_id"]),
                date=sub_date,
                absent_teacher_id=employee.id,
                substitute_teacher_id=sub_emp.id,
                leave_request_id=row.id,
                reason=f"Cover for {employee.user.full_name}",
                status=SubstitutionStatus.pending,
            )
            db.add(sub_row)
            if sub_emp.user_id:
                notify_user(
                    db,
                    school_id=employee.school_id,
                    user_id=sub_emp.user_id,
                    title="Substitution Request",
                    message=f"{employee.user.full_name} has requested you to cover a period on {sub_date}.",
                    category="substitution_request",
                )

    db.flush()
    notify_user(
        db,
        school_id=employee.school_id,
        user_id=employee.user_id,
        title="Leave Application Submitted",
        message=f"Your leave application for {from_date} to {to_date} ({days} day(s)) has been submitted.",
        category="leave_update",
    )
    db.flush()
    return row


def get_leave_substitution_matrix(
    db: Session, school_id: int, leave_request_id: int
) -> dict:
    """Computes every timetable period affected across the leave dates,
    the current provisional substitute (if assigned), and all available free teachers.
    """
    request = db.get(StaffLeaveRequest, leave_request_id)
    if request is None or request.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff leave request not found")

    from app.services import timetable

    periods = affected_periods(db, request)

    items = []
    covered_count = 0
    for day, slot in periods:
        sub = db.scalar(
            select(Substitution).where(
                Substitution.timetable_slot_id == slot.id,
                Substitution.date == day,
            )
        )
        is_covered = sub is not None and sub.substitute_teacher_id is not None
        if is_covered:
            covered_count += 1

        available = timetable.free_teachers(db, school_id, slot.id, day)

        status_val = "unassigned"
        sub_id = None
        sub_teacher_id = None
        sub_teacher_name = None
        if is_covered and sub:
            status_val = sub.status.value if sub.status else "provisional"
            sub_id = sub.id
            sub_teacher_id = sub.substitute_teacher_id
            sub_teacher_name = sub.substitute_teacher.user.full_name if (sub.substitute_teacher and sub.substitute_teacher.user) else None

        free_list = []
        for t in available:
            emp = db.get(Employee, t["teacher_id"])
            emp_code = emp.employee_code if emp else ""
            free_list.append({
                "id": t["teacher_id"],
                "name": t["name"],
                "employee_code": emp_code,
                "teacher_id": t["teacher_id"],
            })

        items.append(
            {
                "date": str(day),
                "slot_id": slot.id,
                "period_id": slot.period_id,
                "period_no": slot.period.period_no,
                "start_time": f"{slot.period.start_time:%H:%M}",
                "end_time": f"{slot.period.end_time:%H:%M}",
                "time": f"{slot.period.start_time:%H:%M} - {slot.period.end_time:%H:%M}",
                "class_section_id": slot.class_section_id,
                "class_label": slot.class_section.label,
                "subject_id": slot.subject_id,
                "subject_name": slot.subject.name if slot.subject else "",
                "room": slot.room,
                "room_number": slot.room,
                "is_covered": is_covered,
                "status": status_val,
                "substitution_id": sub_id,
                "substitute_teacher_id": sub_teacher_id,
                "substitute_teacher_name": sub_teacher_name,
                "free_teachers": free_list,
                "available_teachers": available,
                "substitution": (
                    {
                        "id": sub.id,
                        "substitute_teacher_id": sub.substitute_teacher_id,
                        "substitute_teacher_name": sub_teacher_name,
                        "status": sub.status.value,
                        "reason": sub.reason,
                    }
                    if sub
                    else None
                ),
            }
        )

    return {
        "leave_request_id": request.id,
        "teacher_name": request.employee.user.full_name,
        "from_date": str(request.from_date),
        "to_date": str(request.to_date),
        "days": float(request.days),
        "reason": request.reason,
        "status": request.status.value,
        "total_periods": len(periods),
        "covered_periods": covered_count,
        "is_fully_covered": (covered_count == len(periods)) if periods else True,
        "ready_for_approval": (covered_count == len(periods)) if periods else True,
        "periods": items,
    }


def assign_provisional_substitution(
    db: Session,
    school_id: int,
    user: User,
    leave_request_id: int,
    slot_id: int,
    date: Date,
    substitute_teacher_id: int,
    reason: str | None = None,
) -> Substitution:
    """Assigns a provisional substitute to an affected period while leave is under review."""
    request = db.get(StaffLeaveRequest, leave_request_id)
    if request is None or request.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff leave request not found")

    if request.status != LeaveStatus.applied:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot assign substitutions for a leave in {request.status.value} status",
        )

    slot = db.get(TimetableSlot, slot_id)
    if slot is None or slot.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Timetable slot not found")

    if substitute_teacher_id == request.employee_id:
        raise _bad("The absent teacher cannot substitute for themselves")

    from app.services import timetable

    clash = timetable._teaching_on(db, substitute_teacher_id, slot.day_of_week, slot.period_id)
    if clash is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"That teacher already teaches {clash.class_section.label} in that period",
        )

    also_covering = db.scalar(
        select(Substitution)
        .join(TimetableSlot, TimetableSlot.id == Substitution.timetable_slot_id)
        .where(
            Substitution.date == date,
            Substitution.substitute_teacher_id == substitute_teacher_id,
            TimetableSlot.period_id == slot.period_id,
            Substitution.timetable_slot_id != slot_id,
        )
    )
    if also_covering is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "That teacher is already covering another class in that period",
        )

    away = on_leave(db, substitute_teacher_id, date)
    if away is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"That teacher is on leave on {date}",
        )

    sub = db.scalar(
        select(Substitution).where(
            Substitution.timetable_slot_id == slot.id,
            Substitution.date == date,
        )
    )
    if sub is None:
        sub = Substitution(
            school_id=school_id,
            timetable_slot_id=slot.id,
            date=date,
            absent_teacher_id=request.employee_id,
            substitute_teacher_id=substitute_teacher_id,
            leave_request_id=request.id,
            reason=reason or f"Cover for {request.employee.user.full_name}",
            status=SubstitutionStatus.provisional,
        )
        db.add(sub)
    else:
        sub.substitute_teacher_id = substitute_teacher_id
        sub.leave_request_id = request.id
        sub.reason = reason or f"Cover for {request.employee.user.full_name}"
        sub.status = SubstitutionStatus.provisional

    db.flush()
    return sub


def remove_provisional_substitution(
    db: Session,
    school_id: int,
    user: User,
    leave_request_id: int,
    substitution_id: int,
) -> None:
    """Removes a provisional substitution from an affected period."""
    sub = db.get(Substitution, substitution_id)
    if sub is None or sub.school_id != school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Substitution not found")
    if sub.leave_request_id != leave_request_id:
        raise _bad("Substitution does not belong to this leave request")

    db.delete(sub)
    db.flush()


def approve_teacher_leave_with_substitutions(
    db: Session,
    user: User,
    leave_request_id: int,
    *,
    decision_note: str | None = None,
) -> StaffLeaveRequest:
    """Enforces the strict business gate: A teacher's leave must NOT be granted until
    valid timetable substitutions have been arranged and confirmed for every affected
    period across all requested dates.
    """
    request = db.get(StaffLeaveRequest, leave_request_id)
    if request is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff leave request not found")

    if request.status != LeaveStatus.applied:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This request is already {request.status.value}",
        )

    periods = affected_periods(db, request)
    # The Gating Check:
    missing = []
    for day, slot in periods:
        sub = db.scalar(
            select(Substitution).where(
                Substitution.timetable_slot_id == slot.id,
                Substitution.date == day,
            )
        )
        if (
            sub is None
            or sub.substitute_teacher_id is None
            or sub.status in (SubstitutionStatus.pending, SubstitutionStatus.rejected)
        ):
            status_desc = "unassigned" if (sub is None or sub.substitute_teacher_id is None) else sub.status.value
            missing.append(f"{day} P{slot.period.period_no} ({slot.class_section.label}) [{status_desc}]")

    if missing:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot approve leave: {len(missing)} timetable period(s) lack confirmed substitutes. "
            f"Uncovered: {', '.join(missing[:4])}{'...' if len(missing) > 4 else ''}",
        )

    # 100% of affected slots have substitutes -> Confirm them
    for day, slot in periods:
        sub = db.scalar(
            select(Substitution).where(
                Substitution.timetable_slot_id == slot.id,
                Substitution.date == day,
            )
        )
        if sub is not None:
            sub.status = SubstitutionStatus.assigned
            sub_emp = db.get(Employee, sub.substitute_teacher_id)
            if sub_emp:
                notify_user(
                    db,
                    school_id=request.school_id,
                    user_id=sub_emp.user_id,
                    title="Substitution Duty Assigned",
                    message=(
                        f"You are assigned to cover Class {slot.class_section.label} "
                        f"(Period {slot.period.period_no}, {slot.period.start_time:%H:%M}-{slot.period.end_time:%H:%M}) "
                        f"on {day} for {request.employee.user.full_name}."
                    ),
                    category="substitution_duty",
                )

    request.status = LeaveStatus.approved
    request.decided_by = user.id
    request.decided_at = datetime.now(UTC)
    request.decision_note = decision_note

    from app.services import staff_attendance

    staff_attendance.write_leave(db, request)

    notify_user(
        db,
        school_id=request.school_id,
        user_id=request.employee.user_id,
        title="Leave Approved",
        message=f"Your leave application for {request.from_date} to {request.to_date} ({request.days} day(s)) has been approved. All classes have been substituted.",
        category="leave_update",
    )

    audit.record(
        db,
        actor=user,
        school_id=request.school_id,
        entity_type="staff_leave_request",
        entity_id=request.id,
        action=AuditAction.status_change,
        before={"status": LeaveStatus.applied.value},
        after={"status": LeaveStatus.approved.value},
        reason=decision_note or "Teacher leave approved with full substitutions",
    )
    db.flush()
    return request


def reject_teacher_leave(
    db: Session,
    user: User,
    leave_request_id: int,
    reason: str,
) -> StaffLeaveRequest:
    """Rejects teacher leave application and immediately purges all provisional
    substitutions, returning the master timetable completely intact.
    """
    request = db.get(StaffLeaveRequest, leave_request_id)
    if request is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff leave request not found")

    if request.status != LeaveStatus.applied:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"This request is already {request.status.value}",
        )
    if not reason or not reason.strip():
        raise _bad("Rejection reason is required")

    # RESTORATION / PURGE: Delete all provisional substitutions tied to this leave request
    db.execute(
        Substitution.__table__.delete().where(
            Substitution.leave_request_id == request.id
        )
    )

    request.status = LeaveStatus.rejected
    request.decided_by = user.id
    request.decided_at = datetime.now(UTC)
    request.decision_note = reason.strip()

    notify_user(
        db,
        school_id=request.school_id,
        user_id=request.employee.user_id,
        title="Leave Application Rejected",
        message=f"Your leave application for {request.from_date} to {request.to_date} was rejected. Reason: {reason.strip()}",
        category="leave_update",
    )

    audit.record(
        db,
        actor=user,
        school_id=request.school_id,
        entity_type="staff_leave_request",
        entity_id=request.id,
        action=AuditAction.status_change,
        before={"status": LeaveStatus.applied.value},
        after={"status": LeaveStatus.rejected.value},
        reason=reason.strip(),
    )
    db.flush()
    return request

