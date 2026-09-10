"""route stops: where the halt actually is

Adds latitude/longitude to `route_stops` so the route map can plot a route
from the school's own data rather than a guess.

Both are nullable, and deliberately so. Every stop that already exists was
entered without coordinates, and a school must not be blocked from running
buses until somebody has pinned all of them - the map reports which stops are
still unplaced instead of inventing a position for them.

The range checks are constraints rather than service validation because a
latitude of 200 is wrong for every caller, not only the one route that
happens to check.

Revision ID: c3f61e0a77d2
Revises: b2d85fa3c614
"""

import sqlalchemy as sa
from alembic import op

revision = "c3f61e0a77d2"
down_revision = "b2d85fa3c614"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Batch mode because `tests/test_migrations.py` runs the whole history
    # against SQLite, which has no ALTER for constraints - plain
    # `create_check_constraint` raises NotImplementedError there. On Postgres
    # this emits the same ordinary ALTERs; on SQLite it copies and moves.
    with op.batch_alter_table("route_stops") as batch:
        batch.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("longitude", sa.Float(), nullable=True))
        batch.create_check_constraint(
            "ck_route_stop_latitude",
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
        )
        batch.create_check_constraint(
            "ck_route_stop_longitude",
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
        )


def downgrade() -> None:
    with op.batch_alter_table("route_stops") as batch:
        batch.drop_constraint("ck_route_stop_longitude", type_="check")
        batch.drop_constraint("ck_route_stop_latitude", type_="check")
        batch.drop_column("longitude")
        batch.drop_column("latitude")
