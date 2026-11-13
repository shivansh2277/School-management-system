"""Tests for Direct UPI Intent payment integration, verification, and settlement."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import hmac
import urllib.parse
import pytest
from sqlalchemy import select

from app.models import (
    Enrolment,
    FeeInvoice,
    FeePayment,
    PaymentOrder,
    PaymentOrderStatus,
    PaymentProviderType,
    User,
)
from app.services import fees as svc, school_settings
from app.services.payments import get_payment_provider
from app.services.payments.razorpay import RazorpayProvider

MONTH = {"month": 11, "year": 2026}


def get_first_invoice(client, admin, student_id: int) -> int:
    client.post("/admin/fees/invoices/generate", json=MONTH, headers=admin)
    res = client.get(f"/parent/fees?student_id={student_id}", headers=admin)
    invoices = res.json()
    assert len(invoices) > 0
    return invoices[0]["id"]


def test_create_payment_order_with_configured_merchant_vpa(client, parent, admin, db, ids):
    """Parent creates a payment order for their child's invoice.

    Verifies merchant VPA (configured as 8004400433@pthdfc), amount, and 5-min expiry.
    """
    student_id = ids["student_1"]
    invoice_id = get_first_invoice(client, admin, student_id)

    res = client.post(
        "/parent/fees/orders",
        json={
            "student_id": student_id,
            "invoice_id": invoice_id,
            "provider": "direct_upi",
        },
        headers=parent,
    )
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["status"] == "created"
    assert data["provider"] == "direct_upi"
    assert data["student_id"] == student_id
    assert data["invoice_id"] == invoice_id
    assert Decimal(data["amount"]) > Decimal("0.00")
    assert data["order_no"].startswith("ORD-")
    assert data["tr_ref"].startswith("TR-")

    # Verify NPCI UPI Intent URI format and user's demo VPA
    upi_url = data["upi_intent_url"]
    assert upi_url.startswith("upi://pay?")
    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(upi_url).query)
    assert parsed["pa"] == ["8004400433@pthdfc"]
    assert parsed["pn"] == ["Sunrise Public School"]
    assert parsed["mc"] == ["8220"]
    assert parsed["cu"] == ["INR"]
    assert parsed["tr"] == [data["tr_ref"]]

    # Verify expiry is set 5 minutes into the future
    expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
    now = datetime.now(UTC)
    assert timedelta(minutes=4) < (expires_at - now) <= timedelta(minutes=6)


def test_create_order_idempotent_reuse_within_expiry(client, parent, admin, db, ids):
    """Calling create_order again within the 5-minute window returns the existing active order."""
    student_id = ids["student_1"]
    invoice_id = get_first_invoice(client, admin, student_id)

    res1 = client.post(
        "/parent/fees/orders",
        json={"student_id": student_id, "invoice_id": invoice_id},
        headers=parent,
    )
    assert res1.status_code == 201
    order1 = res1.json()

    # Re-call
    res2 = client.post(
        "/parent/fees/orders",
        json={"student_id": student_id, "invoice_id": invoice_id},
        headers=parent,
    )
    assert res2.status_code == 201
    order2 = res2.json()

    assert order1["id"] == order2["id"]
    assert order1["order_no"] == order2["order_no"]
    assert order1["tr_ref"] == order2["tr_ref"]


def test_order_cancellation_by_parent(client, parent, admin, db, ids):
    """Parent can cancel an active order before submitting UTR."""
    student_id = ids["student_1"]
    invoice_id = get_first_invoice(client, admin, student_id)

    order_res = client.post(
        "/parent/fees/orders",
        json={"student_id": student_id, "invoice_id": invoice_id},
        headers=parent,
    )
    order_id = order_res.json()["id"]

    cancel_res = client.post(
        f"/parent/fees/orders/{order_id}/cancel",
        json={"reason": "Parent changed mind"},
        headers=parent,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Cannot submit UTR on cancelled order
    utr_res = client.post(
        f"/parent/fees/orders/{order_id}/submit-utr",
        json={"bank_utr": "402811223344"},
        headers=parent,
    )
    assert utr_res.status_code in (409, 422)


def test_order_automatic_expiry_transition(client, parent, admin, db, ids):
    """Orders past the 5-minute validity window transition to expired upon status check."""
    student_id = ids["student_1"]
    invoice_id = get_first_invoice(client, admin, student_id)

    order_res = client.post(
        "/parent/fees/orders",
        json={"student_id": student_id, "invoice_id": invoice_id},
        headers=parent,
    )
    order_id = order_res.json()["id"]

    # Artificially expire the order in the database
    order = db.get(PaymentOrder, order_id)
    order.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    # Check status via endpoint
    poll_res = client.get(f"/parent/fees/orders/{order_id}", headers=parent)
    assert poll_res.status_code == 200
    assert poll_res.json()["status"] == "expired"


def test_parent_submit_utr_and_duplicate_prevention(client, parent, admin, db, ids):
    """Parent submits 12-digit UTR, transitions to pending_verification, duplicate UTR rejected."""
    student_id = ids["student_1"]
    invoice_id = get_first_invoice(client, admin, student_id)

    order_res = client.post(
        "/parent/fees/orders",
        json={"student_id": student_id, "invoice_id": invoice_id},
        headers=parent,
    )
    order_id = order_res.json()["id"]

    # Submit valid 12-digit UTR
    utr = "402888991122"
    submit_res = client.post(
        f"/parent/fees/orders/{order_id}/submit-utr",
        json={"bank_utr": utr},
        headers=parent,
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "pending_verification"
    assert submit_res.json()["bank_utr"] == utr

    # Another order attempts to use the same UTR -> HTTP 409 Conflict
    new_order = client.post(
        "/parent/fees/orders",
        json={"student_id": student_id, "invoice_id": invoice_id, "idempotency_key": "distinct-key-99"},
        headers=parent,
    ).json()

    dup_res = client.post(
        f"/parent/fees/orders/{new_order['id']}/submit-utr",
        json={"bank_utr": utr},
        headers=parent,
    )
    assert dup_res.status_code == 409


def test_accounts_desk_verify_utr_approval_and_fifo_settlement(client, parent, admin, accounts_user, db, ids):
    """Accounts desk approves submitted UTR, resulting in FeePayment and FIFO settlement."""
    student_id = ids["student_1"]
    invoice_id = get_first_invoice(client, admin, student_id)

    order_res = client.post(
        "/parent/fees/orders",
        json={"student_id": student_id, "invoice_id": invoice_id},
        headers=parent,
    )
    order_id = order_res.json()["id"]

    utr = "402899112233"
    client.post(
        f"/parent/fees/orders/{order_id}/submit-utr",
        json={"bank_utr": utr},
        headers=parent,
    )

    # Accounts staff views pending verification list
    pending_res = client.get("/admin/fees/orders/pending-verification", headers=accounts_user)
    assert pending_res.status_code == 200
    pending_list = pending_res.json()
    assert any(o["id"] == order_id for o in pending_list)

    # Approve UTR
    verify_res = client.post(
        f"/admin/fees/orders/{order_id}/verify-utr",
        json={"approved": True, "notes": "Amount verified in HDFC school statement"},
        headers=accounts_user,
    )
    assert verify_res.status_code == 200
    settled = verify_res.json()
    assert settled["status"] == "success"
    assert settled["receipt_no"] is not None

    # Verify FeePayment exists in database
    db.expire_all()
    order = db.get(PaymentOrder, order_id)
    assert order.status == PaymentOrderStatus.success
    assert order.fee_payment_id is not None
    payment = db.get(FeePayment, order.fee_payment_id)
    assert payment.method == "upi"
    assert utr in payment.instrument_ref


def test_accounts_desk_verify_utr_rejection(client, parent, accounts_user, admin, db, ids):
    """Accounts desk rejects fraudulent/mismatched UTR without creating FeePayment."""
    student_id = ids["student_1"]
    invoice_id = get_first_invoice(client, admin, student_id)

    order_res = client.post(
        "/parent/fees/orders",
        json={"student_id": student_id, "invoice_id": invoice_id},
        headers=parent,
    )
    order_id = order_res.json()["id"]

    client.post(
        f"/parent/fees/orders/{order_id}/submit-utr",
        json={"bank_utr": "402800000000"},
        headers=parent,
    )

    verify_res = client.post(
        f"/admin/fees/orders/{order_id}/verify-utr",
        json={"approved": False, "notes": "No matching credit on bank statement"},
        headers=accounts_user,
    )
    assert verify_res.status_code == 200
    rejected = verify_res.json()
    assert rejected["status"] == "failed"
    assert rejected["fee_payment_id"] is None


def test_simulated_psp_webhook_hmac_positive_and_tampered(client, parent, admin, db, ids):
    """Simulated PSP webhook settles order on valid HMAC signature, rejects on tampered signature."""
    student_id = ids["student_1"]
    invoice_id = get_first_invoice(client, admin, student_id)

    order_res = client.post(
        "/parent/fees/orders",
        json={"student_id": student_id, "invoice_id": invoice_id},
        headers=parent,
    )
    order_data = order_res.json()
    tr_ref = order_data["tr_ref"]
    amount_str = order_data["amount"]

    secret = str(school_settings.get(db, 1, "fees.upi.webhook_secret"))
    bank_rrn = "402833445566"
    timestamp = datetime.now(UTC).isoformat()

    # 1. Tampered / invalid signature -> 403 Forbidden
    payload = {
        "school_id": 1,
        "tr_ref": tr_ref,
        "amount": amount_str,
        "bank_rrn": bank_rrn,
        "timestamp": timestamp,
        "event": "payment.success",
    }
    tampered_res = client.post(
        "/api/v1/payments/direct-upi/webhook",
        json=payload,
        headers={"X-PSP-Signature": "tampered_signature_hex_000"},
    )
    assert tampered_res.status_code == 403

    # 2. Missing signature -> 401 Unauthorized
    missing_res = client.post("/api/v1/payments/direct-upi/webhook", json=payload)
    assert missing_res.status_code == 401

    # 3. Valid HMAC-SHA256 signature -> 200 OK & atomic settlement
    canonical_data = f"{tr_ref}|{amount_str}|{bank_rrn}|{timestamp}".encode()
    valid_sig = hmac.new(secret.encode(), canonical_data, hashlib.sha256).hexdigest()

    ok_res = client.post(
        "/api/v1/payments/direct-upi/webhook",
        json=payload,
        headers={"X-PSP-Signature": valid_sig},
    )
    assert ok_res.status_code == 200
    res_json = ok_res.json()
    assert res_json["status"] == "success"
    assert res_json["receipt_no"] is not None

    db.expire_all()
    order = db.scalar(select(PaymentOrder).where(PaymentOrder.tr_ref == tr_ref))
    assert order.status == PaymentOrderStatus.success
    assert order.fee_payment_id is not None


def test_razorpay_provider_readiness_stubs():
    """RazorpayProvider exists with full interface contracts and raises 501 until credentials configured."""
    rzp = get_payment_provider(PaymentProviderType.razorpay)
    assert isinstance(rzp, RazorpayProvider)
    assert not rzp.is_configured()

    with pytest.raises(Exception) as exc_info:
        rzp.create_order(
            db=None,  # type: ignore
            school_id=1,
            enrolment_id=1,
            student_id=1,
            amount=Decimal("100.00"),
            invoice_id=None,
            idempotency_key="rzp-test",
        )
    assert "501" in str(exc_info.value) or "Razorpay" in str(exc_info.value)
