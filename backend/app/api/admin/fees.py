from datetime import date as Date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models import FeeInvoice, FeeStructure, InvoiceStatus, Student, User, UserRole
from app.schemas.common import (
    CollectionSummary,
    GenerateInvoicesRequest,
    GenerateInvoicesResult,
    InvoiceOut,
)
from app.services import fees as svc

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_role(UserRole.admin)


@router.get("/fees/structures")
def structures(user: User = Depends(admin_only), db: Session = Depends(get_db)) -> list[dict]:
    return [
        {"id": f.id, "class_name": f.class_name, "monthly_amount": f.monthly_amount}
        for f in db.scalars(select(FeeStructure).order_by(FeeStructure.class_name))
    ]


@router.get("/fees/invoices", response_model=list[InvoiceOut])
def invoices(
    month: int | None = None,
    year: int | None = None,
    status: InvoiceStatus | None = None,
    class_section_id: int | None = None,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> list[InvoiceOut]:
    q = select(FeeInvoice)
    if month is not None:
        q = q.where(FeeInvoice.month == month)
    if year is not None:
        q = q.where(FeeInvoice.year == year)
    if class_section_id is not None:
        q = q.where(
            FeeInvoice.student_id.in_(
                select(Student.id).where(Student.class_section_id == class_section_id)
            )
        )
    rows = list(db.scalars(q.order_by(FeeInvoice.year.desc(), FeeInvoice.month.desc())))
    out = svc.to_out(db, rows)
    # status filter is applied after the overdue refresh, so it matches what is shown
    return [i for i in out if status is None or i.status == status]


@router.post("/fees/invoices/generate", response_model=GenerateInvoicesResult)
def generate(
    body: GenerateInvoicesRequest,
    user: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> GenerateInvoicesResult:
    return svc.generate(db, body.month, body.year, user.school_id)


@router.get("/fees/collection", response_model=CollectionSummary)
def collection(
    year: int | None = None, user: User = Depends(admin_only), db: Session = Depends(get_db)
) -> CollectionSummary:
    return svc.collection(db, year or Date.today().year)
