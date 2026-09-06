from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.models import FeeInvoice, FeePayment, InvoiceStatus, User, UserRole
from app.pdf.receipt import build_receipt
from app.schemas.common import InvoiceOut, PaymentResult
from app.services import fees as svc
from app.services import scoping

router = APIRouter(prefix="/parent", tags=["parent"])
parent_only = require_permission("fees.invoice.read")


def _own_invoice(db: Session, user: User, invoice_id: int) -> FeeInvoice:
    invoice = db.get(FeeInvoice, invoice_id)
    if invoice is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")
    scoping.assert_can_read_student(db, user, invoice.student_id)
    return invoice


@router.get("/fees", response_model=list[InvoiceOut])
def invoices(
    student_id: int | None = None,
    user: User = Depends(parent_only),
    db: Session = Depends(get_db),
) -> list[InvoiceOut]:
    if student_id is not None:
        scoping.assert_can_read_student(db, user, student_id)
        ids = [student_id]
    else:
        ids = scoping.child_ids_for(db, user)
    rows = list(
        db.scalars(
            select(FeeInvoice)
            .where(FeeInvoice.student_id.in_(ids))
            .order_by(FeeInvoice.year.desc(), FeeInvoice.month.desc())
        )
    )
    return svc.to_out(db, rows)


@router.post("/fees/{invoice_id}/pay", response_model=PaymentResult, dependencies=[Depends(require_permission("fees.payment.pay_own"))])
def pay(
    invoice_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> PaymentResult:
    invoice = _own_invoice(db, user, invoice_id)
    return svc.pay(db, invoice.id, actor=user)


@router.get("/fees/{invoice_id}/receipt.pdf")
def receipt(
    invoice_id: int, user: User = Depends(parent_only), db: Session = Depends(get_db)
) -> Response:
    invoice = _own_invoice(db, user, invoice_id)
    if invoice.status != InvoiceStatus.paid:
        raise HTTPException(status.HTTP_409_CONFLICT, "This invoice has not been paid")
    if db.scalar(select(FeePayment).where(FeePayment.invoice_id == invoice.id)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No payment recorded for this invoice")
    filename = f"receipt-{invoice.id}.pdf"
    return Response(
        content=build_receipt(db, invoice.id),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )
