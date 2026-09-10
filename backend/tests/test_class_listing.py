"""How the class list is ordered, and what each class is actually taught.

Both of these read as cosmetic and neither is. `/admin/classes` is the single
endpoint behind every class dropdown in the web app, so an ordering bug here
is one the office meets on Classes, Students, Settings and the fee screens at
the same time. And a subject list that is identical for class 1 and class 10
is not a display problem — it is the school's curriculum being wrong.
"""

from sqlalchemy import select

from app.api.admin.classes import class_order
from app.models import ClassSection
from app.services.common import class_sort_key


class FakeSection:
    """Enough of a ClassSection for the sort key, without touching the DB."""

    def __init__(self, class_name: str, section: str = "A"):
        self.class_name = class_name
        self.section = section


def test_class_ten_sorts_after_class_nine_not_after_class_one():
    """`class_name` is a String, so ordering by the column gave "1", "10", "2"
    and the office saw 10-A wedged between 1-A and 2-A."""
    rows = [FakeSection(n) for n in ["1", "10", "2", "9", "11", "12", "3"]]
    assert [r.class_name for r in sorted(rows, key=class_order)] == [
        "1",
        "2",
        "3",
        "9",
        "10",
        "11",
        "12",
    ]


def test_sections_of_one_class_stay_together_and_in_order():
    rows = [
        FakeSection("10", "B"),
        FakeSection("9", "A"),
        FakeSection("10", "A"),
    ]
    assert [f"{r.class_name}-{r.section}" for r in sorted(rows, key=class_order)] == [
        "9-A",
        "10-A",
        "10-B",
    ]


def test_pre_primary_names_sort_before_the_numbered_classes():
    rows = [FakeSection("1"), FakeSection("UKG"), FakeSection("LKG")]
    ordered = [r.class_name for r in sorted(rows, key=class_order)]
    assert ordered[-1] == "1"
    assert set(ordered[:2]) == {"LKG", "UKG"}


def test_the_endpoint_returns_them_in_that_order(client, admin):
    labels = [c["class_label"] for c in client.get("/admin/classes", headers=admin).json()]
    numbered = [int(x.split("-")[0]) for x in labels]
    assert numbered == sorted(numbered), labels


def test_a_primary_class_is_not_taught_the_same_subjects_as_class_ten(client, admin):
    """Every section held all six subjects, so class 1 was timetabled for
    Social Science and class 10 for EVS. The subject sets are per stage."""
    by_label = {c["class_label"]: set(c["subjects"]) for c in client.get(
        "/admin/classes", headers=admin
    ).json()}
    primary = by_label["1-A"]
    secondary = by_label["10-A"]

    assert primary != secondary
    # EVS is the primary stage's combined science-and-social subject; it is
    # replaced by separate Science and Social Science from class 6.
    assert "Environmental Studies" in primary
    assert "Environmental Studies" not in secondary
    assert {"Science", "Social Science"} <= secondary
    assert "Science" not in primary


def test_every_section_is_taught_something(client, admin, db):
    """A per-stage subject map is easy to leave a hole in; this is the guard."""
    rows = client.get("/admin/classes", headers=admin).json()
    assert len(rows) == len(db.scalars(select(ClassSection)).all())
    for row in rows:
        assert row["subjects"], f"{row['class_label']} has no subjects"


def test_the_shared_key_orders_every_listing_that_uses_it():
    """Five listings ordered by the class_name String independently - classes,
    fee plans, the admission cycle's classes, seat usage and the public portal.
    They share one key now so the next one cannot get it wrong on its own."""
    assert sorted(["10", "1", "2", "9", "11", "12", "3"], key=class_sort_key) == [
        "1", "2", "3", "9", "10", "11", "12",
    ]
    assert class_sort_key("LKG") < class_sort_key("1")
    assert class_sort_key(None) < class_sort_key("1")


def test_the_settings_fee_structure_lists_classes_in_order(client, admin):
    """The Settings screen reads /admin/fees/plans, which had the same bug as
    /admin/classes and was fixed separately from it."""
    plans = client.get("/admin/fees/plans", headers=admin).json()
    numbered = [int(p["class_name"]) for p in plans if (p["class_name"] or "").isdigit()]
    assert numbered == sorted(numbered), [p["class_name"] for p in plans]
