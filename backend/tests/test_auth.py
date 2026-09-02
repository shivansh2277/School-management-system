DEMO = [
    ("admin", "admin@sunrisepublic.edu", "Admin@123"),
    ("teacher", "TCH001", "Teacher@123"),
    ("student", "SPS2024001", "Student@123"),
    ("parent", "9876500001", "Parent@123"),
]


def test_all_four_demo_accounts_log_in(client):
    for role, login_id, password in DEMO:
        r = client.post(
            "/auth/login", json={"role": role, "login_id": login_id, "password": password}
        )
        assert r.status_code == 200, (role, r.text)
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["user"]["role"] == role


def test_wrong_password_is_401(client):
    r = client.post(
        "/auth/login",
        json={"role": "student", "login_id": "SPS2024001", "password": "nope"},
    )
    assert r.status_code == 401


def test_me_carries_the_role_profile(client, student, teacher, parent, admin):
    s = client.get("/auth/me", headers=student).json()
    assert s["admission_no"] == "SPS2024001" and s["class_label"] == "10-A"

    t = client.get("/auth/me", headers=teacher).json()
    assert t["employee_id"] == "TCH001" and "10-A" in t["sections"]

    p = client.get("/auth/me", headers=parent).json()
    assert len(p["children"]) == 2  # the demo parent has two children, so the switcher shows

    a = client.get("/auth/me", headers=admin).json()
    assert a["user"]["role"] == "admin" and a["children"] is None


def test_refresh_returns_a_working_access_token(client):
    tokens = client.post(
        "/auth/login",
        json={"role": "student", "login_id": "SPS2024001", "password": "Student@123"},
    ).json()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    access = r.json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {access}"}).status_code == 200


def test_an_access_token_is_not_a_refresh_token(client):
    tokens = client.post(
        "/auth/login",
        json={"role": "student", "login_id": "SPS2024001", "password": "Student@123"},
    ).json()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401


def test_change_password(client, student):
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
            json={"role": "student", "login_id": "SPS2024001", "password": "Student@1234"},
        ).status_code
        == 200
    )
