import pytest
from app.models import ClassSection, Enrolment, Student, User
from sqlalchemy import select


def test_single_student_id_card_pdf(client, admin, db):
    """Generates single CR80 printable ID card PDF with canonical ENR-{id}."""
    std = db.scalar(select(Student).where(Student.school_id == 1))
    assert std is not None

    res = client.get(f"/admin/students/{std.id}/id-card", headers=admin)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 500
    # PDF magic bytes
    assert res.content[:4] == b"%PDF"


def test_bulk_student_id_cards_pdf(client, admin, db):
    """Generates bulk 8-up A4 printable sheet for a class section."""
    sec = db.scalar(select(ClassSection).where(ClassSection.school_id == 1))
    assert sec is not None

    res = client.get(f"/admin/students/id-cards/bulk?class_section_id={sec.id}", headers=admin)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000
    assert res.content[:4] == b"%PDF"


def test_id_card_unauthorized(client):
    """Unauthenticated request is rejected."""
    res = client.get("/admin/students/1/id-card")
    assert res.status_code == 401
