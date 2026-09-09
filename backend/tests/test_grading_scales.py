"""Grading scales: the rules that keep a published grade honest.

The scale exists so §0.8 can freeze a report card against a *version*. These
tests pin the three things that would otherwise re-grade a document nobody
meant to touch: the version bump, the freeze, and the single active scale.
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import GradeBand
from app.services import grading
from app.services.common import grade_for

CBSE = [
    (Decimal(91), "A1", "Outstanding"),
    (Decimal(33), "D", "Below average"),
    (Decimal(0), "E", "Needs improvement"),
]


def test_the_seeded_scale_is_active_and_grades_the_demo_school(db, ids):
    scale = grading.active_scale(db, ids["school"])
    assert scale is not None and scale.name == "CBSE" and scale.version == 1
    assert grade_for(db, ids["school"], 95) == "A1"


def test_a_scale_whose_lowest_band_is_not_zero_is_refused(db, ids):
    """91/81/71 and nothing below leaves a child on 40% with a blank grade."""
    with pytest.raises(Exception) as e:
        grading.create(
            db,
            ids["school"],
            name="Gappy",
            bands=[(Decimal(91), "A1", None), (Decimal(71), "B1", None)],
        )
    assert "lowest band must start at 0" in str(e.value.detail)


def test_two_bands_cannot_share_a_floor_or_a_grade(db, ids):
    with pytest.raises(Exception) as e:
        grading.create(
            db,
            ids["school"],
            name="Twice",
            bands=[(Decimal(50), "A1", None), (Decimal(50), "B1", None),
                   (Decimal(0), "E", None)],
        )
    assert "same percentage" in str(e.value.detail)

    with pytest.raises(Exception) as e:
        grading.create(
            db,
            ids["school"],
            name="Twice",
            bands=[(Decimal(50), "A1", None), (Decimal(0), "A1", None)],
        )
    assert "same grade" in str(e.value.detail)


def test_reusing_a_name_makes_the_next_version_not_a_second_scale(db, ids):
    second = grading.create(db, ids["school"], name="CBSE", bands=CBSE)
    assert second.version == 2
    assert second.is_active is False, "a new version does not take force by itself"


def test_only_one_scale_is_in_force_at_a_time(db, ids):
    first = grading.active_scale(db, ids["school"])
    second = grading.create(db, ids["school"], name="CBSE", bands=CBSE, activate=True)
    db.flush()
    db.refresh(first)
    assert second.is_active is True
    assert first.is_active is False
    assert grading.active_scale(db, ids["school"]).id == second.id


def test_a_frozen_scale_refuses_an_edit_and_names_the_way_out(db, ids):
    """The freeze is what stops a band edit rewriting an issued report card."""
    scale = grading.active_scale(db, ids["school"])
    grading.freeze(db, scale)
    with pytest.raises(Exception) as e:
        grading.set_bands(db, scale, CBSE)
    assert "published report card" in str(e.value.detail)
    assert "next version" in str(e.value.detail)


def test_freezing_twice_keeps_the_first_timestamp(db, ids):
    scale = grading.active_scale(db, ids["school"])
    first = grading.freeze(db, scale).frozen_at
    assert grading.freeze(db, scale).frozen_at == first


def test_a_grade_can_still_be_read_against_an_old_version(db, ids):
    """The whole point: an edit to the live scale must not move a grade that a
    published document already cited."""
    old = grading.active_scale(db, ids["school"])
    assert grading.grade_in(db, old.id, 95) == "A1"

    # A revision where 95 is only a B1 takes force.
    new = grading.create(
        db,
        ids["school"],
        name="CBSE",
        bands=[(Decimal(96), "A1", None), (Decimal(60), "B1", None),
               (Decimal(0), "E", None)],
        activate=True,
    )
    assert grade_for(db, ids["school"], 95) == "B1", "live screens use the new scale"
    assert grading.grade_in(db, old.id, 95) == "A1", "the cited version is unmoved"
    assert new.version == old.version + 1


def test_bands_are_replaced_wholesale_not_appended(db, ids):
    scale = grading.create(db, ids["school"], name="Short", bands=CBSE)
    grading.set_bands(db, scale, [(Decimal(0), "P", "Pass")])
    rows = db.scalars(
        select(GradeBand).where(GradeBand.grading_scale_id == scale.id)
    ).all()
    assert [r.grade for r in rows] == ["P"]


def test_the_api_creates_activates_and_refuses_a_bad_scale(client, admin, db, ids):
    r = client.post(
        "/admin/grading-scales",
        headers=admin,
        json={
            "name": "Primary",
            "bands": [
                {"min_percent": "80", "grade": "A", "description": "Great"},
                {"min_percent": "0", "grade": "B"},
            ],
            "activate": True,
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["is_active"] is True
    assert r.json()["version"] == 1

    listed = client.get("/admin/grading-scales", headers=admin).json()
    assert {"CBSE", "Primary"} <= {s["name"] for s in listed}
    assert sum(1 for s in listed if s["is_active"]) == 1

    bad = client.post(
        "/admin/grading-scales",
        headers=admin,
        json={"name": "Bad", "bands": [{"min_percent": "40", "grade": "A"}]},
    )
    assert bad.status_code == 422


def test_a_scale_belonging_to_another_school_is_not_found(client, admin, db):
    """404, not 403: the existence of a rival's row is not ours to confirm."""
    from app.models import School

    rival = School(code="RIVAL2", name="Rival Two")
    db.add(rival)
    db.flush()
    theirs = grading.create(db, rival.id, name="Theirs", bands=CBSE)
    db.flush()
    r = client.put(
        f"/admin/grading-scales/{theirs.id}/bands",
        headers=admin,
        json=[{"min_percent": "0", "grade": "P"}],
    )
    assert r.status_code == 404
