"""Library API endpoints for catalogue management and circulation.

Gated on `library.read` and `library.manage`.
Uses canonical Enrollment ID for borrower resolution and circulation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import User
from app.services import library as svc
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled


router = APIRouter(
    prefix="/admin/library",
    tags=["library"],
    dependencies=[Depends(module_enabled("library"))],
)

reader = require_permission("library.read", school_wide=True)
manager = require_permission("library.manage", school_wide=True)


class BookCreate(BaseModel):
    model_config = {"extra": "forbid"}

    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=120)
    isbn: str | None = Field(None, max_length=40)
    publisher: str | None = Field(None, max_length=120)
    edition: str | None = Field(None, max_length=40)
    category: str | None = Field(None, max_length=60)
    shelf_location: str | None = Field(None, max_length=60)
    initial_copies: int = Field(1, ge=1, le=100)
    copies_count: int | None = Field(None, ge=1, le=100)


class AddCopiesInput(BaseModel):
    model_config = {"extra": "forbid"}

    count: int = Field(1, ge=1, le=50)


class IssueBookInput(BaseModel):
    model_config = {"extra": "ignore"}

    copy_barcode: str | None = None
    book_copy_id: int | None = None
    borrower_identifier: str = Field(min_length=1)  # ENR-123 or admission_no or id
    loan_days: int = Field(14, ge=1, le=60)
    remarks: str | None = Field(None, max_length=255)


class ReturnBookInput(BaseModel):
    model_config = {"extra": "ignore"}

    copy_barcode_or_loan_id: str | None = None
    condition: str = Field("good", pattern=r"^(good|fair|damaged|lost)$")
    remarks: str | None = Field(None, max_length=255)


class RenewBookInput(BaseModel):
    model_config = {"extra": "forbid"}

    additional_days: int = Field(14, ge=1, le=30)


class SettleFineInput(BaseModel):
    model_config = {"extra": "forbid"}

    action: str = Field("paid", pattern=r"^(paid|waived)$")
    reason: str = Field(min_length=3, max_length=255)


@router.get("/books")
def list_books(
    q: str | None = Query(None),
    category: str | None = Query(None),
    available_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    books, total = svc.search_books(
        db, user.school_id, query=q, category=category, available_only=available_only, page=page, page_size=page_size
    )
    return {
        "items": [
            {
                "id": b.id,
                "isbn": b.isbn,
                "title": b.title,
                "author": b.author,
                "publisher": b.publisher,
                "category": b.category,
                "total_copies": b.total_copies,
                "available_copies": b.available_copies,
                "shelf_location": b.shelf_location,
                "copies": [
                    {
                        "id": c.id,
                        "barcode": c.barcode,
                        "status": c.status,
                    }
                    for c in b.copies
                ],
            }
            for b in books
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/books", status_code=status.HTTP_201_CREATED)
def create_book(
    body: BookCreate,
    user: User = Depends(manager),
    db: Session = Depends(get_db),
) -> dict:
    book = svc.create_book(
        db,
        user.school_id,
        title=body.title,
        author=body.author,
        isbn=body.isbn,
        publisher=body.publisher,
        edition=body.edition,
        category=body.category,
        shelf_location=body.shelf_location,
        initial_copies=body.copies_count or body.initial_copies,
    )
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies,
    }


@router.get("/books/{book_id}")
def get_book(
    book_id: int,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    b = svc.get_book(db, user.school_id, book_id)
    return {
        "id": b.id,
        "isbn": b.isbn,
        "title": b.title,
        "author": b.author,
        "publisher": b.publisher,
        "category": b.category,
        "total_copies": b.total_copies,
        "available_copies": b.available_copies,
        "shelf_location": b.shelf_location,
        "copies": [
            {
                "id": c.id,
                "accession_no": c.accession_no,
                "barcode": c.barcode,
                "status": c.status,
            }
            for c in b.copies
        ],
    }


@router.post("/books/{book_id}/copies")
def add_copies(
    book_id: int,
    body: AddCopiesInput,
    user: User = Depends(manager),
    db: Session = Depends(get_db),
) -> dict:
    book = svc.add_copies(db, user.school_id, book_id, count=body.count)
    return {
        "id": book.id,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies,
    }


@router.get("/borrowers/lookup")
def lookup_borrower(
    q: str = Query(..., min_length=1),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    return svc.lookup_borrower(db, user.school_id, q)


@router.get("/borrowers/{identifier}")
def lookup_borrower_by_path(
    identifier: str,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    return svc.lookup_borrower(db, user.school_id, identifier)


@router.post("/loans/issue", status_code=status.HTTP_201_CREATED)
def issue_loan(
    body: IssueBookInput,
    user: User = Depends(manager),
    db: Session = Depends(get_db),
) -> dict:
    loan = svc.issue_book(
        db,
        user.school_id,
        copy_barcode=body.copy_barcode,
        book_copy_id=body.book_copy_id,
        borrower_identifier=body.borrower_identifier,
        issued_by=user,
        loan_days=body.loan_days,
        remarks=body.remarks,
    )
    return {
        "id": loan.id,
        "book_copy_id": loan.book_copy_id,
        "enrolment_id": loan.enrolment_id,
        "issued_on": str(loan.issued_on),
        "due_date": str(loan.due_date),
        "status": loan.status,
    }


@router.post("/loans/return")
def return_loan(
    body: ReturnBookInput,
    user: User = Depends(manager),
    db: Session = Depends(get_db),
) -> dict:
    return svc.return_book(
        db,
        user.school_id,
        copy_barcode_or_loan_id=body.copy_barcode_or_loan_id,
        returned_by=user,
        condition=body.condition,
        remarks=body.remarks,
    )


@router.post("/loans/{loan_id}/return")
def return_loan_by_id(
    loan_id: int,
    body: ReturnBookInput = None,
    user: User = Depends(manager),
    db: Session = Depends(get_db),
) -> dict:
    b = body or ReturnBookInput()
    return svc.return_book(
        db,
        user.school_id,
        loan_id=loan_id,
        returned_by=user,
        condition=b.condition,
        remarks=b.remarks,
    )


@router.post("/loans/{loan_id}/renew")
def renew_loan(
    loan_id: int,
    body: RenewBookInput,
    user: User = Depends(manager),
    db: Session = Depends(get_db),
) -> dict:
    loan = svc.renew_book(
        db, user.school_id, loan_id=loan_id, actor=user, additional_days=body.additional_days
    )
    return {
        "id": loan.id,
        "due_date": str(loan.due_date),
        "renewal_count": loan.renewal_count,
    }


@router.post("/loans/{loan_id}/settle-fine")
def settle_fine(
    loan_id: int,
    body: SettleFineInput,
    user: User = Depends(manager),
    db: Session = Depends(get_db),
) -> dict:
    loan = svc.settle_fine(
        db, user.school_id, loan_id=loan_id, action=body.action, reason=body.reason, actor=user
    )
    return {
        "id": loan.id,
        "fine_amount": float(loan.fine_amount),
        "fine_paid": loan.fine_paid,
        "remarks": loan.remarks,
    }


@router.get("/loans")
def list_loans(
    status: str | None = Query(None),  # "active" | "overdue" | "returned" | "fines"
    enrolment_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> dict:
    items, total = svc.list_loans(
        db,
        user.school_id,
        status_filter=status,
        enrolment_id=enrolment_id,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
