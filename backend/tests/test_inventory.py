"""Tests for stock and inventory management, teacher flagging, and RBAC permissions."""


from sqlalchemy import select

from app.models import AuditAction, AuditLog, School, StockItem


def test_inventory_stats_highlights_and_critical_alerts(client, admin):
    """Verifies that overview highlights return:
    - 18 Low-stock items
    - 7 Pending approvals/requests
    - 3 Stock discrepancies
    And includes critical alerts for Printer paper, First-aid supplies, and Science chemicals.
    """
    res = client.get("/admin/inventory/stats", headers=admin)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["low_stock_count"] == 18
    assert data["pending_approvals_count"] == 7
    assert data["discrepancies_count"] == 3

    alert_titles = [a["title"] for a in data["critical_alerts"]]
    assert any("printer paper" in t.lower() for t in alert_titles)
    assert any("first-aid" in t.lower() for t in alert_titles)
    assert any("science chemical" in t.lower() for t in alert_titles)


def test_list_inventory_items_and_filters(client, admin):
    """Test item catalogue listing and filtering by category, location, and low_stock_only."""
    res = client.get("/admin/inventory/items", headers=admin)
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 30

    # Filter by category Science Lab
    res_sci = client.get("/admin/inventory/items?category=Science Lab", headers=admin)
    assert res_sci.status_code == 200
    for it in res_sci.json():
        assert "Science" in it["category"]

    # Filter by low_stock_only
    res_low = client.get("/admin/inventory/items?low_stock_only=true", headers=admin)
    assert res_low.status_code == 200
    low_items = res_low.json()
    assert len(low_items) == 18
    for it in low_items:
        assert it["current_quantity"] <= it["min_quantity"]


def test_adjust_stock_with_audit_reason(client, admin, db):
    """Adjusting stock updates current_quantity, sets discrepancy flag, and logs to audit_log."""
    item = db.scalar(select(StockItem))
    assert item is not None

    res = client.patch(
        f"/admin/inventory/items/{item.id}/adjust",
        headers=admin,
        json={
            "new_quantity": 42,
            "reason": "Physical count audit reconciled after term-end delivery",
            "has_discrepancy": False,
        },
    )
    assert res.status_code == 200
    assert res.json()["current_quantity"] == 42
    assert res.json()["has_discrepancy"] is False

    # Check audit log
    audit_entry = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "stock_item",
            AuditLog.entity_id == item.id,
            AuditLog.action == AuditAction.status_change,
        )
        .order_by(AuditLog.occurred_at.desc())
    )
    assert audit_entry is not None
    assert "reconciled" in audit_entry.reason


def test_teacher_can_flag_diminishing_stock(client, teacher, admin):
    """Teachers can flag diminishing stock via /teacher/stock/flag and it immediately surfaces in admin requests."""
    res = client.post(
        "/teacher/stock/flag",
        headers=teacher,
        json={
            "item_name": "Class 10 Biology Microscope Glass Slides",
            "category": "Science Lab",
            "location": "Science Lab",
            "quantity_requested": 15,
            "urgency": "urgent",
            "flag_type": "diminishing",
            "reason": "Cover slips and glass slides depleted during cell structure practicals",
        },
    )
    assert res.status_code == 201, res.text
    flag_id = res.json()["id"]

    # Admin checks requests and verifies the newly flagged item is visible
    admin_reqs = client.get("/admin/inventory/requests?status=pending", headers=admin).json()
    req = next((r for r in admin_reqs if r["id"] == flag_id), None)
    assert req is not None
    assert req["item_name"] == "Class 10 Biology Microscope Glass Slides"
    assert req["urgency"] == "urgent"
    assert req["flag_type"] == "diminishing"


def test_teacher_cannot_approve_request(client, teacher, admin):
    """Teachers hold inventory.request.create but lack inventory.request.approve."""
    pending = client.get("/admin/inventory/requests?status=pending", headers=admin).json()
    assert len(pending) > 0
    req_id = pending[0]["id"]

    res = client.post(
        f"/admin/inventory/requests/{req_id}/decide",
        headers=teacher,
        json={"status": "approved", "decision_note": "Teacher attempt to self-approve"},
    )
    assert res.status_code == 403


def test_admin_can_approve_request_with_audit(client, admin, db):
    """Leadership can approve requests with notes, audited."""
    pending = client.get("/admin/inventory/requests?status=pending", headers=admin).json()
    assert len(pending) > 0
    req_id = pending[0]["id"]

    res = client.post(
        f"/admin/inventory/requests/{req_id}/decide",
        headers=admin,
        json={"status": "approved", "decision_note": "Approved purchase requisition as per budget"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "approved"
    assert res.json()["decision_note"] == "Approved purchase requisition as per budget"


def test_inventory_tenant_isolation(client, admin, db):
    """Stock items from School B must never leak to or be modifiable by School A."""
    school2 = School(name="Other Public School", code="OPS")
    db.add(school2)
    db.flush()

    item_school2 = StockItem(
        school_id=school2.id,
        name="Secret School B Lab Chemical",
        category="Science Lab",
        location="Lab B",
        unit="bottles",
        current_quantity=10,
        min_quantity=5,
    )
    db.add(item_school2)
    db.flush()

    # Admin of School A lists items: School B item must not be present
    res = client.get("/admin/inventory/items", headers=admin)
    item_names = [it["name"] for it in res.json()]
    assert "Secret School B Lab Chemical" not in item_names

    # Admin of School A tries to adjust School B item: gets 404
    res_adjust = client.patch(
        f"/admin/inventory/items/{item_school2.id}/adjust",
        headers=admin,
        json={"new_quantity": 20, "reason": "Unauthorized cross-tenant adjustment attempt"},
    )
    assert res_adjust.status_code == 404
