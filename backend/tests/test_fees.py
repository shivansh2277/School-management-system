from datetime import date

from app.pdf.receipt import amount_in_words


def test_amount_in_words_indian_numbering():
    from decimal import Decimal

    assert amount_in_words(Decimal("2800.00")) == "Rupees Two Thousand Eight Hundred Only"
    assert amount_in_words(Decimal("100000")) == "Rupees One Lakh Only"
    assert amount_in_words(Decimal("2500.50")) == (
        "Rupees Two Thousand Five Hundred and Fifty Paise Only"
    )


def test_invoice_generation_is_idempotent(client, admin, db):
    body = {"month": 12, "year": 2026}
    first = client.post("/admin/fees/invoices/generate", json=body, headers=admin).json()
    second = client.post("/admin/fees/invoices/generate", json=body, headers=admin).json()
    # Every active student in the school, whatever the demo size is.
    from app.models import Student

    expected = db.query(Student).count()
    assert first["created"] == expected and first["skipped"] == 0
    assert second["created"] == 0 and second["skipped"] == expected


def pending_invoice(client, parent):
    invoices = client.get("/parent/fees", headers=parent).json()
    return next(i for i in invoices if i["status"] != "paid")


def test_paying_twice_is_a_conflict(client, parent, admin):
    client.post("/admin/fees/invoices/generate", json={"month": 12, "year": 2026}, headers=admin)
    invoice = pending_invoice(client, parent)
    first = client.post(f"/parent/fees/{invoice['id']}/pay", headers=parent)
    assert first.status_code == 200
    assert first.json()["receipt_no"].startswith("SPS/RCP/")
    assert first.json()["txn_ref"].startswith("SIM-")
    assert client.post(f"/parent/fees/{invoice['id']}/pay", headers=parent).status_code == 409


def test_receipt_numbers_are_unique(client, parent, admin, db):
    client.post("/admin/fees/invoices/generate", json={"month": 12, "year": 2026}, headers=admin)
    issued = []
    for _ in range(2):
        invoice = pending_invoice(client, parent)
        issued.append(client.post(f"/parent/fees/{invoice['id']}/pay", headers=parent).json())
    assert len({r["receipt_no"] for r in issued}) == 2

    from app.models import FeePayment

    all_numbers = [p.receipt_no for p in db.query(FeePayment).all()]
    assert len(all_numbers) == len(set(all_numbers))


def test_pending_past_its_due_date_presents_as_overdue(client, parent, admin, db):
    from app.models import FeeInvoice, InvoiceStatus

    invoice = db.query(FeeInvoice).first()
    invoice.status = InvoiceStatus.pending
    invoice.due_date = date(2020, 1, 10)
    db.flush()
    rows = client.get("/admin/fees/invoices", headers=admin).json()
    row = next(r for r in rows if r["id"] == invoice.id)
    assert row["status"] == "overdue"


def test_collection_total_equals_the_sum_of_payments(client, admin, db):
    from decimal import Decimal

    from app.models import FeeInvoice, FeePayment

    year = db.query(FeeInvoice).first().year
    expected = sum(
        (p.amount for p in db.query(FeePayment).join(
            FeeInvoice, FeeInvoice.id == FeePayment.invoice_id
        ).filter(FeeInvoice.year == year)),
        Decimal(0),
    )
    body = client.get(f"/admin/fees/collection?year={year}", headers=admin).json()
    assert Decimal(body["collected"]) == expected
    assert Decimal(body["outstanding"]) == Decimal(body["billed"]) - Decimal(body["collected"])


def test_receipt_pdf_is_served_only_after_payment(client, parent, admin):
    client.post("/admin/fees/invoices/generate", json={"month": 12, "year": 2026}, headers=admin)
    invoice = pending_invoice(client, parent)
    assert client.get(f"/parent/fees/{invoice['id']}/receipt.pdf", headers=parent).status_code == 409

    client.post(f"/parent/fees/{invoice['id']}/pay", headers=parent)
    r = client.get(f"/parent/fees/{invoice['id']}/receipt.pdf", headers=parent)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
