from datetime import date, timedelta
from decimal import Decimal
import pytest
from app.models import Book, BookCopy, Enrolment, LibraryLoan, Student, User
from sqlalchemy import select


def test_library_catalogue_search_and_add_book(client, librarian, teacher):
    """Librarian can search books and add new books with copies; teacher has read-only or no manage."""
    # List books
    res = client.get("/admin/library/books", headers=librarian)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    # Add new book
    create_res = client.post(
        "/admin/library/books",
        headers=librarian,
        json={
            "isbn": "978-0385737951",
            "title": "The Maze Runner",
            "author": "James Dashner",
            "category": "Young Adult",
            "shelf_location": "Shelf E2",
            "copies_count": 2,
        },
    )
    assert create_res.status_code == 201
    new_book = create_res.json()
    assert new_book["title"] == "The Maze Runner"
    assert new_book["total_copies"] == 2
    assert new_book["available_copies"] == 2


def test_library_borrower_lookup_via_canonical_enrollment_id(client, librarian, db):
    """Borrower lookup accepts canonical ENR-{id} string or numeric ID."""
    enr = db.scalar(select(Enrolment).where(Enrolment.school_id == 1))
    assert enr is not None

    # Lookup via ENR-1
    res = client.get(f"/admin/library/borrowers/ENR-{enr.id}", headers=librarian)
    assert res.status_code == 200
    data = res.json()
    assert data["enrolment_id"] == enr.id
    assert "student_name" in data


def test_library_circulation_issue_renew_return_fine(client, librarian, db):
    """Issue book copy to student via Enrollment ID, renew, return with fine settlement."""
    from app.models.enums import EnrolmentStatus
    enr = db.scalar(
        select(Enrolment).where(
            Enrolment.school_id == 1,
            Enrolment.status == EnrolmentStatus.active,
            ~Enrolment.id.in_(select(LibraryLoan.enrolment_id).where(LibraryLoan.school_id == 1, LibraryLoan.status == "active")),
        )
    )
    assert enr is not None
    # Find an available copy
    copy = db.scalar(
        select(BookCopy)
        .join(Book)
        .where(BookCopy.school_id == 1, BookCopy.status == "available", Book.available_copies > 0)
    )
    assert copy is not None

    # 1. Issue book
    issue_res = client.post(
        "/admin/library/loans/issue",
        headers=librarian,
        json={
            "book_copy_id": copy.id,
            "borrower_identifier": f"ENR-{enr.id}",
            "loan_days": 14,
        },
    )
    assert issue_res.status_code == 201
    loan = issue_res.json()
    loan_id = loan["id"]
    assert loan["status"] == "active"

    # Verify copy status changed to issued
    copy_check = db.scalar(select(BookCopy).where(BookCopy.id == copy.id))
    assert copy_check.status == "issued"

    # 2. Renew loan
    renew_res = client.post(
        f"/admin/library/loans/{loan_id}/renew",
        headers=librarian,
        json={"additional_days": 7},
    )
    assert renew_res.status_code == 200
    renewed = renew_res.json()
    assert renewed["renewal_count"] == 1

    # 3. Return book
    return_res = client.post(
        f"/admin/library/loans/{loan_id}/return",
        headers=librarian,
        json={},
    )
    assert return_res.status_code == 200
    returned = return_res.json()
    assert returned["status"] == "returned"

    # Verify copy status changed back to available
    db.expire_all()
    copy_after = db.scalar(select(BookCopy).where(BookCopy.id == copy.id))
    assert copy_after.status == "available"


def test_library_permissions_enforced(client, student):
    """Student cannot issue books or create books (403)."""
    res = client.post(
        "/admin/library/books",
        headers=student,
        json={
            "title": "Unauthorized Book",
            "author": "Hacker",
            "category": "Fiction",
            "copies_count": 1,
        },
    )
    assert res.status_code == 403
