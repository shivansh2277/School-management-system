"""Tests for public announcements workflow and endpoints."""

import pytest


def test_public_announcement_workflow(client, admin):
    # 1. Publish a private notice
    r_priv = client.post(
        "/admin/notices",
        json={
            "title": "Internal Staff Meeting",
            "body": "Mandatory staff briefing in the auditorium at 3 PM.",
            "audience": "teachers",
            "category": "General",
            "is_public": False,
        },
        headers=admin,
    )
    assert r_priv.status_code == 201, r_priv.text
    priv_id = r_priv.json()["id"]

    # 2. Publish a public announcement with category and pinned state
    r_pub = client.post(
        "/admin/notices",
        json={
            "title": "Admissions Open for Academic Session 2026-27",
            "body": "Sunrise School announces admissions open for Nursery to Grade XI. Apply online via the admission portal.",
            "audience": "all",
            "category": "Admission",
            "is_public": True,
            "is_pinned": True,
            "summary": "Admissions now open for Nursery through Grade 11. Early applications encouraged.",
        },
        headers=admin,
    )
    assert r_pub.status_code == 201, r_pub.text
    pub_data = r_pub.json()
    assert pub_data["is_public"] is True
    assert pub_data["category"] == "Admission"
    assert pub_data["is_pinned"] is True
    pub_id = pub_data["id"]

    # 3. Publish a second public announcement (Academic)
    r_pub2 = client.post(
        "/admin/notices",
        json={
            "title": "Annual Science & STEM Exhibition 2026",
            "body": "Students from Grades 6 to 12 will present robotics and working models at the central courtyard.",
            "audience": "all",
            "category": "Academic",
            "is_public": True,
            "is_pinned": False,
            "summary": "Annual STEM showcase featuring student robotics and experimental setups.",
        },
        headers=admin,
    )
    assert r_pub2.status_code == 201
    pub2_id = r_pub2.json()["id"]

    # 4. Query public announcements endpoint without authentication
    r_list = client.get("/public/SPS/announcements")
    assert r_list.status_code == 200
    items = r_list.json()
    item_ids = [item["id"] for item in items]

    # Verify public announcements are visible and private notice is excluded
    assert pub_id in item_ids
    assert pub2_id in item_ids
    assert priv_id not in item_ids

    # Verify pinned item comes first
    pub_index = item_ids.index(pub_id)
    pub2_index = item_ids.index(pub2_id)
    assert pub_index < pub2_index

    # 5. Query with category filter
    r_cat = client.get("/public/SPS/announcements?category=Admission")
    assert r_cat.status_code == 200
    cat_items = r_cat.json()
    assert any(item["id"] == pub_id for item in cat_items)
    assert not any(item["id"] == pub2_id for item in cat_items)

    # 6. Retrieve single public announcement
    r_single = client.get(f"/public/SPS/announcements/{pub_id}")
    assert r_single.status_code == 200
    assert r_single.json()["title"] == "Admissions Open for Academic Session 2026-27"
    assert r_single.json()["category"] == "Admission"

    # 7. Attempt to retrieve private notice via public endpoint -> 404
    r_bad = client.get(f"/public/SPS/announcements/{priv_id}")
    assert r_bad.status_code == 404

    # 8. Query default public announcements endpoint (/public/announcements)
    r_default = client.get("/public/announcements")
    assert r_default.status_code == 200
    default_ids = [item["id"] for item in r_default.json()]
    assert pub_id in default_ids
