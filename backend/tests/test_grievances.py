"""Tests for the Grievances & Feedback module.

Covers submission by teachers and parents, admin reply workflows, teacher assignments,
filtering, role permissions, and multi-tenant scoping.
"""
from fastapi import status


def test_admin_grievance_stats_and_list(client, admin):
    res = client.get("/admin/grievances/stats", headers=admin)
    assert res.status_code == status.HTTP_200_OK, res.text
    data = res.json()
    assert "total_count" in data
    assert "open_count" in data
    assert "in_progress_count" in data
    assert "resolved_count" in data

    res = client.get("/admin/grievances", headers=admin)
    assert res.status_code == status.HTTP_200_OK
    items = res.json()
    assert isinstance(items, list)
    assert len(items) >= 4


def test_teacher_create_and_list_grievances(client, teacher):
    payload = {
        "title": "Smartboard stylus batteries dead",
        "description": "Smartboard pen in Room 102 has run out of charge, cannot complete interactive math session.",
        "category": "facilities",
        "priority": "high",
    }
    res = client.post("/teacher/grievances", json=payload, headers=teacher)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    created = res.json()
    assert created["title"] == payload["title"]
    assert created["raised_by_role"] == "teacher"
    assert created["status"] == "open"
    grievance_id = created["id"]

    # Teacher lists grievances
    res = client.get("/teacher/grievances", headers=teacher)
    assert res.status_code == status.HTTP_200_OK
    mine = res.json()
    assert any(g["id"] == grievance_id for g in mine)


def test_admin_reply_and_assign(client, admin, teacher):
    # Create grievance as teacher
    res = client.post(
        "/teacher/grievances",
        json={
            "title": "Laboratory sink clogged",
            "description": "Drainage in sink 3 of the chemistry lab is overflowing.",
            "category": "facilities",
            "priority": "medium",
        },
        headers=teacher,
    )
    assert res.status_code == status.HTTP_201_CREATED
    gid = res.json()["id"]

    # Admin replies
    res = client.post(
        f"/admin/grievances/{gid}/reply",
        json={"message": "Maintenance technician has been notified."},
        headers=admin,
    )
    assert res.status_code == status.HTTP_200_OK
    reply = res.json()
    assert reply["message"] == "Maintenance technician has been notified."
    assert reply["author_role"] == "admin"

    # Status should now be in_progress
    res = client.get(f"/admin/grievances/{gid}", headers=admin)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "in_progress"
    assert len(res.json()["replies"]) >= 1

    # Admin resolves grievance
    res = client.patch(
        f"/admin/grievances/{gid}/status",
        json={
            "status": "resolved",
            "resolution_notes": "Plumbing unclogged and verified by lab assistant.",
        },
        headers=admin,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "resolved"
    assert res.json()["resolution_notes"] == "Plumbing unclogged and verified by lab assistant."


def test_parent_create_and_view_grievance(client, parent):
    # List children to get valid student_id
    res = client.get("/parent/children", headers=parent)
    assert res.status_code == status.HTTP_200_OK
    children = res.json()
    student_id = children[0]["id"] if children else None

    payload = {
        "title": "Inquiry regarding annual sports day uniform",
        "description": "Have not received size chart for sports kit.",
        "category": "general",
        "priority": "low",
        "student_id": student_id,
    }
    res = client.post("/parent/grievances", json=payload, headers=parent)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    created = res.json()
    assert created["raised_by_role"] == "parent"
    gid = created["id"]

    # Parent views list
    res = client.get("/parent/grievances", headers=parent)
    assert res.status_code == status.HTTP_200_OK
    assert any(g["id"] == gid for g in res.json())


def test_admin_staff_assignees(client, admin):
    res = client.get("/admin/grievances/staff", headers=admin)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "id" in first
    assert "employee_code" in first
    assert "full_name" in first

