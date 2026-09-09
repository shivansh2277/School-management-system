import pytest

from tests.conftest import _login_id_in

DEMO = [
    ("admin", "admin@sunrisepublic.edu", "Admin@123"),
    ("teacher", "TCH001", "Teacher@123"),
    ("parent", "9876500001", "Parent@123"),
]


@pytest.fixture()
def STUDENT_LOGIN(db):
    """Admission numbers come from a sequence now, so the demo student is found
    by where they sit rather than by a literal."""
    return _login_id_in(db, "10")


def test_all_four_demo_accounts_log_in(client, STUDENT_LOGIN):
    for role, login_id, password in [*DEMO, ("student", STUDENT_LOGIN, "Student@123")]:
        r = client.post(
            "/auth/login", json={"role": role, "login_id": login_id, "password": password}
        )
        assert r.status_code == 200, (role, r.text)
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["user"]["role"] == role


def test_wrong_password_is_401(client, STUDENT_LOGIN):
    r = client.post(
        "/auth/login",
        json={"role": "student", "login_id": STUDENT_LOGIN, "password": "nope"},
    )
    assert r.status_code == 401


def test_me_carries_the_role_profile(client, student, teacher, parent, admin, STUDENT_LOGIN):
    s = client.get("/auth/me", headers=student).json()
    assert s["admission_no"] == STUDENT_LOGIN and s["class_label"] == "10-A"

    t = client.get("/auth/me", headers=teacher).json()
    assert t["employee_id"] == "TCH001" and "10-A" in t["sections"]

    p = client.get("/auth/me", headers=parent).json()
    assert len(p["children"]) == 2  # the demo parent has two children, so the switcher shows

    a = client.get("/auth/me", headers=admin).json()
    assert a["user"]["role"] == "admin" and a["children"] is None


def test_refresh_returns_a_working_access_token(client, STUDENT_LOGIN):
    tokens = client.post(
        "/auth/login",
        json={"role": "student", "login_id": STUDENT_LOGIN, "password": "Student@123"},
    ).json()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    access = r.json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {access}"}).status_code == 200


def test_an_access_token_is_not_a_refresh_token(client, STUDENT_LOGIN):
    tokens = client.post(
        "/auth/login",
        json={"role": "student", "login_id": STUDENT_LOGIN, "password": "Student@123"},
    ).json()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401


def test_change_password(client, student, STUDENT_LOGIN):
    assert (
        client.post(
            "/auth/change-password",
            json={"old_password": "wrong", "new_password": "Student@1234"},
            headers=student,
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/auth/change-password",
            json={"old_password": "Student@123", "new_password": "Student@1234"},
            headers=student,
        ).status_code
        == 204
    )
    assert (
        client.post(
            "/auth/login",
            json={"role": "student", "login_id": STUDENT_LOGIN, "password": "Student@1234"},
        ).status_code
        == 200
    )


def test_me_reports_which_modules_the_school_has_on(client, admin, db, admin_user):
    """The clients hide a switched-off module, and most staff cannot read the
    configuration screen to find out: `admin.settings.read` is not held by the
    fee collector, accountant, exam controller or transport manager. So the
    fact travels on /auth/me, beside the permissions the nav is already built
    from."""
    from app.services import school_settings

    school_settings.set_many(db, admin_user, {"feature.transport": False, "feature.fees": True})

    body = client.get("/auth/me", headers=admin).json()
    assert "fees" in body["modules"]
    assert "transport" not in body["modules"]

    school_settings.set_many(db, admin_user, {"feature.transport": True})
    assert "transport" in client.get("/auth/me", headers=admin).json()["modules"]


def test_every_reported_module_is_a_real_module(client, admin):
    from app.core.modules import BY_CODE

    for code in client.get("/auth/me", headers=admin).json()["modules"]:
        assert code in BY_CODE
