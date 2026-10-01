"""Library circulation and catalogue service.

Directly unified with enrolments via canonical Enrollment ID (ENR-{id}).
No separate library cards or duplicate student records.
Preserves books, copies, historical loans, and overdue fines.
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import re

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    Book,
    BookCopy,
    Employee,
    Enrolment,
    EnrolmentStatus,
    LibraryLoan,
    Student,
    User,
)
from app.services import audit
from app.services.common import current_enrolment


DEFAULT_LOAN_DAYS = 14
DAILY_OVERDUE_FINE = Decimal("5.00")
MAX_ACTIVE_LOANS_PER_STUDENT = 3
MAX_UNPAID_FINE_BLOCK = Decimal("100.00")


def _get_staff_employee(db: Session, school_id: int, user: User) -> Employee:
    emp = db.scalar(select(Employee).where(Employee.user_id == user.id))
    if emp is None:
        emp = db.scalar(select(Employee).join(User).where(User.school_id == school_id))
    if emp is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "No employee record associated with issuing user")
    return emp


def search_books(
    db: Session,
    school_id: int,
    query: str | None = None,
    category: str | None = None,
    available_only: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Book], int]:
    stmt = select(Book).where(Book.school_id == school_id)
    if query:
        q_clean = f"%{query.strip()}%"
        stmt = stmt.where(
            or_(
                Book.title.ilike(q_clean),
                Book.author.ilike(q_clean),
                Book.isbn.ilike(q_clean),
                Book.publisher.ilike(q_clean),
            )
        )
    if category:
        stmt = stmt.where(Book.category == category.strip())
    if available_only:
        stmt = stmt.where(Book.available_copies > 0)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(Book.title).offset((page - 1) * page_size).limit(page_size)
    books = list(db.scalars(stmt).all())
    return books, total


def get_book(db: Session, school_id: int, book_id: int) -> Book:
    b = db.scalar(
        select(Book).where(Book.id == book_id, Book.school_id == school_id)
    )
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    return b


def create_book(
    db: Session,
    school_id: int,
    title: str,
    author: str,
    isbn: str | None = None,
    publisher: str | None = None,
    edition: str | None = None,
    category: str | None = None,
    shelf_location: str | None = None,
    initial_copies: int = 1,
) -> Book:
    if initial_copies < 1:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Copies count must be at least 1")

    book = Book(
        school_id=school_id,
        isbn=isbn.strip() if isbn else None,
        title=title.strip(),
        author=author.strip(),
        publisher=publisher.strip() if publisher else None,
        category=category.strip() if category else "General",
        shelf_location=shelf_location.strip() if shelf_location else None,
        total_copies=initial_copies,
        available_copies=initial_copies,
    )
    db.add(book)
    db.flush()

    acc_count = db.scalar(select(func.count(BookCopy.id)).where(BookCopy.school_id == school_id)) or 0
    for idx in range(initial_copies):
        acc_no = f"ACC-{school_id}-{acc_count + idx + 1:04d}"
        barcode = f"BC-{acc_no}"
        copy = BookCopy(
            school_id=school_id,
            book_id=book.id,
            accession_no=acc_no,
            barcode=barcode,
            status="available",
        )
        db.add(copy)

    db.commit()
    return book


def add_copies(db: Session, school_id: int, book_id: int, count: int = 1) -> Book:
    book = get_book(db, school_id, book_id)
    if count < 1:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Must add at least 1 copy")

    acc_count = db.scalar(select(func.count(BookCopy.id)).where(BookCopy.school_id == school_id)) or 0
    book.total_copies += count
    book.available_copies += count

    for i in range(count):
        acc_no = f"ACC-{school_id}-{acc_count + i + 1:04d}"
        barcode = f"BC-{acc_no}"
        copy = BookCopy(
            school_id=school_id,
            book_id=book.id,
            accession_no=acc_no,
            barcode=barcode,
            status="available",
        )
        db.add(copy)

    db.commit()
    return book


def parse_enrolment_id(identifier: str | int) -> int | None:
    """Parse 'ENR-42' or 42 into integer enrolment id."""
    if isinstance(identifier, int):
        return identifier
    s = str(identifier).strip()
    if s.upper().startswith("ENR-"):
        parts = s.split("-")
        if len(parts) >= 2 and parts[1].isdigit():
            return int(parts[1])
    if s.isdigit():
        return int(s)
    return None


def lookup_borrower(db: Session, school_id: int, identifier: str) -> dict:
    """Find student borrower by Enrollment ID ('ENR-123'), admission_no, or name."""
    clean_id = str(identifier).strip()
    enrolment: Enrolment | None = None

    enr_id = parse_enrolment_id(clean_id)
    if enr_id:
        enrolment = db.scalar(
            select(Enrolment).where(
                Enrolment.id == enr_id,
                Enrolment.school_id == school_id,
            )
        )

    if enrolment is None:
        # Try matching by student admission_no or name
        student = db.scalar(
            select(Student)
            .join(User, User.id == Student.user_id)
            .where(
                Student.school_id == school_id,
                or_(
                    Student.admission_no.ilike(clean_id),
                    User.full_name.ilike(f"%{clean_id}%"),
                ),
            )
        )
        if student:
            enrolment = current_enrolment(db, student.id)

    if enrolment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Borrower '{identifier}' not found")

    student = enrolment.student
    active_loans = list(
        db.scalars(
            select(LibraryLoan).where(
                LibraryLoan.enrolment_id == enrolment.id,
                LibraryLoan.status == "active",
            )
        ).all()
    )

    # Compute unpaid fines
    unpaid_fines = db.scalar(
        select(func.coalesce(func.sum(LibraryLoan.fine_amount), Decimal("0"))).where(
            LibraryLoan.enrolment_id == enrolment.id,
            LibraryLoan.fine_paid.is_(False),
            LibraryLoan.fine_amount > Decimal("0"),
        )
    ) or Decimal("0")

    # Check for overdue active loans
    has_overdue = any(loan.due_date < date.today() for loan in active_loans)
    is_eligible = (
        enrolment.status == EnrolmentStatus.active
        and len(active_loans) < MAX_ACTIVE_LOANS_PER_STUDENT
        and unpaid_fines <= MAX_UNPAID_FINE_BLOCK
        and not has_overdue
    )

    reasons = []
    if enrolment.status != EnrolmentStatus.active:
        reasons.append(f"Student enrolment status is {enrolment.status.value}")
    if len(active_loans) >= MAX_ACTIVE_LOANS_PER_STUDENT:
        reasons.append(f"Reached maximum limit of {MAX_ACTIVE_LOANS_PER_STUDENT} active loans")
    if unpaid_fines > MAX_UNPAID_FINE_BLOCK:
        reasons.append(f"Unpaid fine balance of ₹{unpaid_fines} exceeds limit")
    if has_overdue:
        reasons.append("Has overdue book(s) that must be returned first")

    return {
        "enrolment_id": enrolment.id,
        "enrollment_code": f"ENR-{enrolment.id}",
        "student_id": student.id,
        "admission_no": student.admission_no,
        "student_name": student.user.full_name if student.user else "",
        "class_label": enrolment.class_section.label if enrolment.class_section else "",
        "roll_no": enrolment.roll_no,
        "active_loans_count": len(active_loans),
        "unpaid_fines": float(unpaid_fines),
        "is_eligible": is_eligible,
        "ineligibility_reasons": reasons,
        "active_loans": [
            {
                "loan_id": loan.id,
                "book_id": loan.book_copy.book_id if loan.book_copy else None,
                "book_title": loan.book_copy.book.title if loan.book_copy and loan.book_copy.book else "",
                "barcode": loan.book_copy.barcode if loan.book_copy else "",
                "issued_on": loan.issued_on.isoformat() if loan.issued_on else None,
                "due_date": str(loan.due_date),
                "is_overdue": loan.due_date < date.today(),
            }
            for loan in active_loans
        ],
    }


def issue_book(
    db: Session,
    school_id: int,
    copy_barcode: str | None = None,
    book_copy_id: int | None = None,
    borrower_identifier: str | int = "",
    issued_by: User = None,
    loan_days: int = DEFAULT_LOAN_DAYS,
    remarks: str | None = None,
) -> LibraryLoan:
    borrower = lookup_borrower(db, school_id, str(borrower_identifier))
    if not borrower["is_eligible"]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Borrower is not eligible: " + "; ".join(borrower["ineligibility_reasons"]),
        )

    copy = None
    if book_copy_id:
        copy = db.scalar(
            select(BookCopy).where(
                BookCopy.id == book_copy_id,
                BookCopy.school_id == school_id,
            )
        )
    elif copy_barcode:
        copy = db.scalar(
            select(BookCopy).where(
                BookCopy.barcode == copy_barcode.strip(),
                BookCopy.school_id == school_id,
            )
        )
    if copy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Book copy not found")
    if copy.status != "available":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Book copy is currently {copy.status}"
        )

    book = copy.book
    if book.available_copies <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "No copies available for this book")

    staff_emp = _get_staff_employee(db, school_id, issued_by)

    loan = LibraryLoan(
        school_id=school_id,
        book_copy_id=copy.id,
        enrolment_id=borrower["enrolment_id"],
        issued_on=date.today(),
        due_date=date.today() + timedelta(days=loan_days),
        issued_by_id=staff_emp.id,
        status="active",
        fine_amount=Decimal("0.00"),
        fine_paid=False,
        renewal_count=0,
        remarks=remarks,
    )
    db.add(loan)
    copy.status = "issued"
    book.available_copies = max(0, book.available_copies - 1)

    audit.record(
        db,
        actor=issued_by,
        school_id=school_id,
        entity_type="library_loan",
        entity_id=copy.id,
        action=AuditAction.create,
        after={
            "copy_barcode": copy.barcode,
            "book_title": book.title,
            "enrolment_id": borrower["enrolment_id"],
            "due_date": str(loan.due_date),
        },
        reason="Book loan issued",
    )
    db.commit()
    return loan


def return_book(
    db: Session,
    school_id: int,
    copy_barcode_or_loan_id: str | None = None,
    loan_id: int | None = None,
    returned_by: User = None,
    condition: str = "good",
    remarks: str | None = None,
) -> dict:
    loan: LibraryLoan | None = None
    target_id = loan_id
    clean = str(copy_barcode_or_loan_id or "").strip()

    if target_id:
        loan = db.scalar(
            select(LibraryLoan).where(
                LibraryLoan.id == target_id,
                LibraryLoan.school_id == school_id,
                LibraryLoan.status == "active",
            )
        )
    elif clean.isdigit():
        loan = db.scalar(
            select(LibraryLoan).where(
                LibraryLoan.id == int(clean),
                LibraryLoan.school_id == school_id,
                LibraryLoan.status == "active",
            )
        )

    if loan is None and clean:
        copy = db.scalar(
            select(BookCopy).where(
                BookCopy.barcode == clean,
                BookCopy.school_id == school_id,
            )
        )
        if copy:
            loan = db.scalar(
                select(LibraryLoan).where(
                    LibraryLoan.book_copy_id == copy.id,
                    LibraryLoan.status == "active",
                )
            )

    if loan is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Active loan not found for '{copy_barcode_or_loan_id or loan_id}'"
        )

    today = date.today()
    overdue_days = max(0, (today - loan.due_date).days)
    fine = Decimal(str(overdue_days)) * DAILY_OVERDUE_FINE

    loan.returned_on = today
    loan.status = "returned"
    loan.fine_amount = fine
    loan.fine_paid = (fine == Decimal("0.00"))
    if remarks:
        loan.remarks = f"{loan.remarks or ''} | Return: {remarks}".strip(" |")

    copy = loan.book_copy
    copy.status = "available" if condition != "lost" else "lost"

    book = copy.book
    if copy.status == "available":
        book.available_copies = min(book.total_copies, book.available_copies + 1)

    audit.record(
        db,
        actor=returned_by,
        school_id=school_id,
        entity_type="library_loan",
        entity_id=loan.id,
        action=AuditAction.update,
        after={
            "loan_id": loan.id,
            "copy_barcode": copy.barcode,
            "fine_amount": str(fine),
            "overdue_days": overdue_days,
        },
        reason="Book returned",
    )
    db.commit()

    return {
        "loan_id": loan.id,
        "copy_barcode": copy.barcode,
        "book_title": book.title,
        "due_date": str(loan.due_date),
        "returned_on": str(loan.returned_on),
        "overdue_days": overdue_days,
        "fine_amount": float(fine),
        "fine_paid": loan.fine_paid,
        "status": loan.status,
    }


def renew_book(
    db: Session,
    school_id: int,
    loan_id: int,
    actor: User,
    additional_days: int = DEFAULT_LOAN_DAYS,
) -> LibraryLoan:
    loan = db.scalar(
        select(LibraryLoan).where(
            LibraryLoan.id == loan_id,
            LibraryLoan.school_id == school_id,
            LibraryLoan.status == "active",
        )
    )
    if loan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Active loan not found")

    old_due = loan.due_date
    loan.due_date = max(loan.due_date, date.today()) + timedelta(days=additional_days)
    loan.renewal_count += 1

    audit.record(
        db,
        actor=actor,
        school_id=school_id,
        entity_type="library_loan",
        entity_id=loan.id,
        action=AuditAction.update,
        before={"due_date": str(old_due)},
        after={"due_date": str(loan.due_date), "renewal_count": loan.renewal_count},
        reason="Loan renewed",
    )
    db.commit()
    return loan


def settle_fine(
    db: Session,
    school_id: int,
    loan_id: int,
    action: str,  # "paid" | "waived"
    reason: str,
    actor: User,
) -> LibraryLoan:
    if action not in ("paid", "waived"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Action must be 'paid' or 'waived'")
    loan = db.scalar(
        select(LibraryLoan).where(
            LibraryLoan.id == loan_id,
            LibraryLoan.school_id == school_id,
        )
    )
    if loan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Loan not found")
    if loan.fine_paid:
        raise HTTPException(status.HTTP_409_CONFLICT, "Fine is already settled")

    loan.fine_paid = True
    loan.remarks = f"{loan.remarks or ''} | Fine {action}: {reason}".strip(" |")

    audit.record(
        db,
        actor=actor,
        school_id=school_id,
        entity_type="library_loan",
        entity_id=loan.id,
        action=AuditAction.update,
        after={"fine_paid": True, "action": action, "reason": reason},
        reason=f"Library fine {action}: {reason}",
    )
    db.commit()
    return loan


def list_loans(
    db: Session,
    school_id: int,
    status_filter: str | None = None,  # "active" | "overdue" | "returned" | "fines"
    enrolment_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    stmt = (
        select(LibraryLoan)
        .join(BookCopy, BookCopy.id == LibraryLoan.book_copy_id)
        .join(Book, Book.id == BookCopy.book_id)
        .join(Enrolment, Enrolment.id == LibraryLoan.enrolment_id)
        .join(Student, Student.id == Enrolment.student_id)
        .join(User, User.id == Student.user_id)
        .where(LibraryLoan.school_id == school_id)
    )

    today = date.today()
    if status_filter == "active":
        stmt = stmt.where(LibraryLoan.status == "active")
    elif status_filter == "overdue":
        stmt = stmt.where(LibraryLoan.status == "active", LibraryLoan.due_date < today)
    elif status_filter == "returned":
        stmt = stmt.where(LibraryLoan.status == "returned")
    elif status_filter == "fines":
        stmt = stmt.where(LibraryLoan.fine_paid.is_(False), LibraryLoan.fine_amount > Decimal("0"))

    if enrolment_id:
        stmt = stmt.where(LibraryLoan.enrolment_id == enrolment_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(LibraryLoan.id.desc()).offset((page - 1) * page_size).limit(page_size)
    loans = list(db.scalars(stmt).all())

    out = []
    for l in loans:
        student = l.enrolment.student if l.enrolment else None
        out.append(
            {
                "id": l.id,
                "book_copy_id": l.book_copy_id,
                "barcode": l.book_copy.barcode if l.book_copy else "",
                "accession_no": l.book_copy.accession_no if l.book_copy else "",
                "book_id": l.book_copy.book_id if l.book_copy else None,
                "book_title": l.book_copy.book.title if l.book_copy and l.book_copy.book else "",
                "book_author": l.book_copy.book.author if l.book_copy and l.book_copy.book else "",
                "enrolment_id": l.enrolment_id,
                "enrollment_code": f"ENR-{l.enrolment_id}",
                "student_id": student.id if student else None,
                "student_name": student.user.full_name if student and student.user else "",
                "admission_no": student.admission_no if student else "",
                "class_label": l.enrolment.class_section.label if l.enrolment and l.enrolment.class_section else "",
                "issued_on": str(l.issued_on),
                "due_date": str(l.due_date),
                "returned_on": str(l.returned_on) if l.returned_on else None,
                "is_overdue": (l.status == "active" and l.due_date < today),
                "fine_amount": float(l.fine_amount),
                "fine_paid": l.fine_paid,
                "status": l.status,
                "renewal_count": l.renewal_count,
                "remarks": l.remarks,
            }
        )
    return out, total
