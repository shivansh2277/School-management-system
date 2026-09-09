"""The public admission portal — the only unauthenticated surface in the
product (§0.13, §5.1.3).

What is tested here is mostly what the portal must *not* do: confirm which
schools exist, leak another family's application, or let a script fill the
register.
"""


import pytest
from sqlalchemy import select

from app.models import Application, School

BASE = "/public/SPS/admission"


@pytest.fixture(autouse=True)
def _school_code(db):
    """The seeded school's code, so the tests read the way the URL does."""
    assert db.scalar(select(School.code)) == "SPS"


def _payload(**over):
    body = {
        "first_name": "Ishaan",
        "last_name": "Kapoor",
        "date_of_birth": "2019-08-20",
        "gender": "male",
        "class_applying_for": "1",
        "guardians": [
            {
                "relation": "mother",
                "full_name": "Sneha Kapoor",
                "mobile": "9877700001",
                "is_primary": True,
            }
        ],
        "information_accuracy": True,
        "school_rules_accepted": True,
        "data_processing_consent": True,
    }
    body.update(over)
    return body


def test_a_parent_can_see_what_is_open_without_logging_in(client):
    body = client.get(f"{BASE}/open").json()
    assert body["school"]["name"] == "Sunrise Public School"
    assert body["cycle"]["application_fee"] == "500.00"
    assert {c["class_name"] for c in body["classes"]} == {"1", "6", "9"}
    # Seats offered are public; seats already taken are not.
    assert "filled" not in str(body)


def test_an_unknown_school_looks_the_same_as_a_closed_one(client):
    assert client.get("/public/NOPE/admission/open").status_code == 404


def test_a_complete_application_lands_as_submitted(client, db):
    r = client.post(f"{BASE}/apply", json=_payload())
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["application_no"].startswith("APP")
    # §0.13: it waits for staff. Nothing is decided by the portal.
    assert body["status"] == "submitted"

    app = db.scalar(
        select(Application).where(Application.application_no == body["application_no"])
    )
    assert app.created_by is None  # nobody at the school typed it
    assert app.declarations["submitted_from"] == "public_portal"


def test_consent_is_not_optional_and_not_pre_ticked(client):
    r = client.post(f"{BASE}/apply", json=_payload(data_processing_consent=False))
    assert r.status_code == 422
    assert "consent to process this data" in r.json()["detail"]


def test_the_form_needs_one_main_contact(client):
    two = [
        {"relation": "father", "full_name": "A", "mobile": "9877700002", "is_primary": True},
        {"relation": "mother", "full_name": "B", "mobile": "9877700003", "is_primary": True},
    ]
    assert client.post(f"{BASE}/apply", json=_payload(guardians=two)).status_code == 422


def test_a_filled_honeypot_is_accepted_and_discarded(client, db):
    """Telling a bot it was caught only teaches it to try again differently."""
    before = db.scalar(select(Application.id).order_by(Application.id.desc()))
    r = client.post(f"{BASE}/apply", json=_payload(website="http://buy-cheap.example"))
    assert r.status_code == 201
    assert r.json()["application_no"] is None
    after = db.scalar(select(Application.id).order_by(Application.id.desc()))
    assert before == after  # nothing was written


def test_a_script_is_rate_limited_by_address(client):
    for i in range(5):
        r = client.post(
            f"{BASE}/apply",
            json=_payload(first_name=f"Child{i}", guardians=[
                {
                    "relation": "father",
                    "full_name": "Repeat Parent",
                    "mobile": f"98777100{i:02d}",
                    "is_primary": True,
                }
            ]),
        )
        assert r.status_code == 201, r.text
    r = client.post(f"{BASE}/apply", json=_payload(first_name="Sixth"))
    assert r.status_code == 429
    assert "call the school office" in r.json()["detail"]


def test_status_needs_both_the_number_and_the_date_of_birth(client):
    created = client.post(f"{BASE}/apply", json=_payload()).json()
    number = created["application_no"]

    ok = client.get(f"{BASE}/status?application_no={number}&date_of_birth=2019-08-20")
    assert ok.status_code == 200
    assert ok.json()["status"] == "submitted"

    # Right number, wrong child: the same answer as a number that never
    # existed, so this cannot be walked to find other people's children.
    wrong_dob = client.get(
        f"{BASE}/status?application_no={number}&date_of_birth=2019-08-21"
    )
    missing = client.get(
        f"{BASE}/status?application_no=APP2025-99999&date_of_birth=2019-08-20"
    )
    assert wrong_dob.status_code == missing.status_code == 404
    assert wrong_dob.json() == missing.json()


def test_the_portal_closes_with_the_module_flag(client, admin):
    client.put(
        "/admin/configuration",
        json={"values": {"feature.admission": False}},
        headers=admin,
    )
    assert client.get(f"{BASE}/open").status_code == 404
    assert client.post(f"{BASE}/apply", json=_payload()).status_code == 404


def test_a_school_can_turn_online_applications_off_by_itself(client, admin, db):
    from app.models import AdmissionCycle

    cycle = db.scalar(select(AdmissionCycle))
    r = client.patch(
        f"/admin/admission/cycles/{cycle.id}",
        json={"allow_online_applications": False},
        headers=admin,
    )
    assert r.status_code == 200
    assert client.get(f"{BASE}/open").status_code == 409
    assert client.post(f"{BASE}/apply", json=_payload()).status_code == 409
