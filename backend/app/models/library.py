from datetime import date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase


class Book(TenantBase):
    """A book title in the library catalog."""

    __tablename__ = "books"
    __table_args__ = (
        Index("ix_books_title", "school_id", "title"),
        Index("ix_books_category", "school_id", "category"),
    )

    isbn: Mapped[str | None] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(120), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="General")
    total_copies: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    available_copies: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    shelf_location: Mapped[str | None] = mapped_column(String(40))

    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")


class BookCopy(TenantBase):
    """An individual physical copy of a book, identified by a unique accession number."""

    __tablename__ = "book_copies"
    __table_args__ = (
        UniqueConstraint("school_id", "accession_no", name="uq_book_copy_accession"),
    )

    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    accession_no: Mapped[str] = mapped_column(String(40), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")  # "available", "issued", "lost", "reference_only"

    book = relationship("Book", back_populates="copies", lazy="joined")


class LibraryLoan(TenantBase):
    """A circulation record: book copy issued to an enrolled student (via Enrollment ID)
    or a staff member.
    """

    __tablename__ = "library_loans"
    __table_args__ = (
        Index("ix_loan_enrolment", "school_id", "enrolment_id", "status"),
        Index("ix_loan_employee", "school_id", "employee_id", "status"),
        Index("ix_loan_due_date", "school_id", "due_date", "status"),
    )

    book_copy_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("book_copies.id"), nullable=False)
    # Connected directly to the enrolled-student record (Enrollment ID). Zero separate library cards!
    enrolment_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("enrolments.id"))
    employee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id"))
    issued_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id"), nullable=False)
    issued_on: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    returned_on: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # "active", "returned", "overdue", "lost"
    fine_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    fine_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    renewal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remarks: Mapped[str | None] = mapped_column(Text)

    book_copy = relationship("BookCopy", lazy="joined")
    enrolment = relationship("Enrolment", lazy="joined")
    employee = relationship("Employee", foreign_keys=[employee_id], lazy="joined")
    issued_by = relationship("Employee", foreign_keys=[issued_by_id], lazy="joined")
