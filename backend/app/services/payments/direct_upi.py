"""Direct UPI Intent payment provider implementation with NPCI intent generation and dual verification."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import hmac
import json
from typing import Any
import urllib.parse
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    FeeInvoice,
    FeePayment,
    PaymentMethodType,
    PaymentOrder,
    PaymentOrderStatus,
    PaymentProviderType,
    User,
)
from app.services import audit, fees as svc, school_settings
from app.services.payments.base import PaymentGatewayProvider


class DirectUPIProvider(PaymentGatewayProvider):
    """Direct UPI Intent provider for native mobile intent launching and verified reconciliation."""

    def create_order(
        self,
        db: Session,
        school_id: int,
        enrolment_id: int,
        student_id: int,
        amount: Decimal,
        invoice_id: int | None,
        idempotency_key: str,
        note: str | None = None,
    ) -> PaymentOrder:
        # Check idempotency
        existing = db.scalar(
            select(PaymentOrder).where(
                PaymentOrder.school_id == school_id,
                PaymentOrder.idempotency_key == idempotency_key,
            )
        )
        if existing:
            # Check expiry
            now = datetime.now(UTC)
            if existing.status in (PaymentOrderStatus.created, PaymentOrderStatus.pending) and now > existing.expires_at:
                existing.status = PaymentOrderStatus.expired
                db.flush()
            return existing

        now = datetime.now(UTC)
        order_no = f"ORD-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        tr_ref = f"TR-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        vpa = str(school_settings.get(db, school_id, "fees.upi.merchant_vpa"))
        merchant_name = str(school_settings.get(db, school_id, "fees.upi.merchant_name"))
        mcc = str(school_settings.get(db, school_id, "fees.upi.mcc"))

        tx_note = note or f"Fees {order_no}"
        # Build NPCI standardized UPI intent deep link
        upi_params = {
            "pa": vpa,
            "pn": merchant_name,
            "mc": mcc,
            "tr": tr_ref,
            "tn": tx_note[:40],
            "am": f"{amount:.2f}",
            "cu": "INR",
        }
        upi_url = f"upi://pay?{urllib.parse.urlencode(upi_params)}"

        order = PaymentOrder(
            school_id=school_id,
            order_no=order_no,
            enrolment_id=enrolment_id,
            student_id=student_id,
            invoice_id=invoice_id,
            amount=amount,
            currency="INR",
            provider=PaymentProviderType.direct_upi,
            method=PaymentMethodType.upi,
            status=PaymentOrderStatus.created,
            tr_ref=tr_ref,
            upi_intent_url=upi_url,
            expires_at=now + timedelta(minutes=5),
            idempotency_key=idempotency_key,
            metadata_json=json.dumps({"merchant_vpa": vpa, "merchant_name": merchant_name, "mcc": mcc}),
        )
        db.add(order)
        db.flush()

        audit.record(
            db,
            actor=None,
            school_id=school_id,
            entity_type="payment_order",
            entity_id=order.id,
            action=AuditAction.create,
            after={"order_no": order.order_no, "amount": str(order.amount), "provider": "direct_upi"},
            reason=f"Created Direct UPI order for {amount}",
        )
        return order

    def verify_webhook(
        self,
        db: Session,
        school_id: int,
        payload: dict[str, Any],
        signature: str | None,
    ) -> PaymentOrder:
        """Validates simulated/real acquiring bank PSP webhook and triggers settlement."""
        secret = str(school_settings.get(db, school_id, "fees.upi.webhook_secret"))

        # Verify HMAC signature
        if not signature:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing webhook signature header")

        tr_ref = payload.get("tr_ref")
        amount_str = payload.get("amount")
        bank_rrn = payload.get("bank_rrn", "")
        timestamp = payload.get("timestamp", "")
        event = payload.get("event", "payment.success")

        canonical_data = f"{tr_ref}|{amount_str}|{bank_rrn}|{timestamp}".encode()
        expected_sig = hmac.new(secret.encode(), canonical_data, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid webhook HMAC signature")

        order = db.scalar(
            select(PaymentOrder).where(
                PaymentOrder.school_id == school_id,
                PaymentOrder.tr_ref == tr_ref,
            )
        )
        if not order:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Payment order with tr {tr_ref} not found")

        # Verify amount match
        if Decimal(amount_str) != order.amount:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Webhook amount does not match order amount")

        # Idempotent response if already confirmed
        if order.status == PaymentOrderStatus.success:
            return order

        if event == "payment.success":
            # Atomic settlement into official fee ledger
            fee_payment = svc.collect(
                db,
                enrolment_id=order.enrolment_id,
                amount=order.amount,
                idempotency_key=f"order-{order.order_no}",
                method="upi",
                instrument_ref=f"UPI-{bank_rrn or tr_ref}",
                actor=None,
            )
            order.status = PaymentOrderStatus.success
            order.bank_utr = bank_rrn or order.bank_utr
            order.fee_payment_id = fee_payment.id
            order.fee_payment = fee_payment
            order.verified_at = datetime.now(UTC)
            order.verification_notes = f"Settled via PSP Webhook (RRN: {bank_rrn})"
            db.flush()

            audit.record(
                db,
                actor=None,
                school_id=school_id,
                entity_type="payment_order",
                entity_id=order.id,
                action=AuditAction.update,
                after={"status": order.status.value, "receipt_no": fee_payment.receipt_no},
                reason=f"Payment verified via webhook; receipt {fee_payment.receipt_no} issued",
            )
        else:
            order.status = PaymentOrderStatus.failed
            order.verification_notes = payload.get("error", "Payment failed at bank")
            db.flush()

        return order

    def submit_utr(
        self,
        db: Session,
        order: PaymentOrder,
        bank_utr: str,
    ) -> PaymentOrder:
        """Parent submits 12-digit UPI reference number for manual reconciliation."""
        clean_utr = bank_utr.strip().upper()
        if len(clean_utr) < 8 or len(clean_utr) > 30:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid UTR format. Typically 12 alphanumeric characters.")

        if order.status in (PaymentOrderStatus.success, PaymentOrderStatus.cancelled, PaymentOrderStatus.expired):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Cannot submit UTR for an order in state '{order.status.value}'",
            )

        # Check for duplicate UTR used by another settled/pending order
        duplicate = db.scalar(
            select(PaymentOrder).where(
                PaymentOrder.school_id == order.school_id,
                PaymentOrder.bank_utr == clean_utr,
                PaymentOrder.id != order.id,
                PaymentOrder.status.in_([PaymentOrderStatus.success, PaymentOrderStatus.pending_verification]),
            )
        )
        if duplicate:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "This UPI transaction reference (UTR) is already registered for another order",
            )

        order.bank_utr = clean_utr
        order.utr_submitted_at = datetime.now(UTC)
        order.status = PaymentOrderStatus.pending_verification
        db.flush()

        audit.record(
            db,
            actor=None,
            school_id=order.school_id,
            entity_type="payment_order",
            entity_id=order.id,
            action=AuditAction.update,
            after={"status": order.status.value, "bank_utr": clean_utr},
            reason=f"Parent submitted UTR {clean_utr}",
        )
        return order

    def verify_utr(
        self,
        db: Session,
        order: PaymentOrder,
        approved: bool,
        actor: User,
        notes: str | None = None,
    ) -> PaymentOrder:
        """Accounts desk confirms or rejects a submitted UTR against the bank statement."""
        if order.status == PaymentOrderStatus.success:
            return order

        if order.status != PaymentOrderStatus.pending_verification and not order.bank_utr:
            raise HTTPException(status.HTTP_409_CONFLICT, "Order does not have a submitted UTR for verification")

        now = datetime.now(UTC)
        if approved:
            # Atomic settlement through FIFO fee engine
            fee_payment = svc.collect(
                db,
                enrolment_id=order.enrolment_id,
                amount=order.amount,
                idempotency_key=f"order-{order.order_no}",
                method="upi",
                instrument_ref=f"UTR-{order.bank_utr}",
                actor=actor,
            )
            order.status = PaymentOrderStatus.success
            order.fee_payment_id = fee_payment.id
            order.fee_payment = fee_payment
            order.verified_by = actor.id
            order.verified_at = now
            order.verification_notes = notes or "UTR verified by accounts officer"
            db.flush()

            audit.record(
                db,
                actor=actor,
                school_id=order.school_id,
                entity_type="payment_order",
                entity_id=order.id,
                action=AuditAction.update,
                after={"status": order.status.value, "fee_payment_id": fee_payment.id, "receipt_no": fee_payment.receipt_no},
                reason=f"Accounts officer approved UTR {order.bank_utr}; receipt {fee_payment.receipt_no}",
            )
        else:
            order.status = PaymentOrderStatus.failed
            order.verified_by = actor.id
            order.verified_at = now
            order.verification_notes = notes or "UTR verification rejected"
            db.flush()

            audit.record(
                db,
                actor=actor,
                school_id=order.school_id,
                entity_type="payment_order",
                entity_id=order.id,
                action=AuditAction.update,
                after={"status": order.status.value},
                reason=f"Accounts officer rejected UTR {order.bank_utr}: {notes}",
            )

        return order

    def cancel_order(
        self,
        db: Session,
        order: PaymentOrder,
        reason: str | None = None,
    ) -> PaymentOrder:
        if order.status in (PaymentOrderStatus.success, PaymentOrderStatus.pending_verification):
            raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot cancel an order in state '{order.status.value}'")

        order.status = PaymentOrderStatus.cancelled
        order.verification_notes = reason or "Cancelled by user"
        db.flush()

        audit.record(
            db,
            actor=None,
            school_id=order.school_id,
            entity_type="payment_order",
            entity_id=order.id,
            action=AuditAction.update,
            after={"status": order.status.value},
            reason=f"Order cancelled: {reason}",
        )
        return order

    def check_status(
        self,
        db: Session,
        order: PaymentOrder,
    ) -> PaymentOrder:
        # Automatic expiry transition
        if order.status in (PaymentOrderStatus.created, PaymentOrderStatus.pending):
            if datetime.now(UTC) > order.expires_at:
                order.status = PaymentOrderStatus.expired
                db.flush()
        return order
