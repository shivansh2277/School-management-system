"""The migrations must produce a schema the application can actually use.

The rest of the suite builds its schema with `Base.metadata.create_all`, straight
from the models, so it never sees what the migrations produce. That gap hid a
real bug: a batch `alter_column` dropped `updated_at`'s server_default, leaving a
NOT NULL column with no default, and every insert into it failed. Nothing in a
model-built schema could catch it.

This is the slowest test in the suite by some margin, which is the price of
exercising the thing that actually runs in production.
"""

import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent


def _run(args: list[str], db_url: str) -> subprocess.CompletedProcess:
    import os

    env = {
        **os.environ,
        "DATABASE_URL": db_url,
        "TEST_DATABASE_URL": db_url,
        "BCRYPT_ROUNDS": "4",
    }
    return subprocess.run(
        args, cwd=BACKEND, env=env, capture_output=True, text=True, timeout=300
    )


@pytest.fixture()
def migrated_db(tmp_path):
    db_file = tmp_path / "migrated.db"
    url = f"sqlite:///{db_file.as_posix()}"
    result = _run([sys.executable, "-m", "alembic", "upgrade", "head"], url)
    assert result.returncode == 0, result.stderr[-3000:]
    return url


def test_migrations_apply_to_an_empty_database(migrated_db):
    """Every revision runs, in order, against nothing."""
    import sqlite3

    path = migrated_db.replace("sqlite:///", "")
    tables = {
        r[0]
        for r in sqlite3.connect(path).execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    for expected in (
        "schools",
        "academic_years",
        "enrolments",
        "roles",
        "permissions",
        "audit_log",
        "number_sequences",
        "jobs",
        "scheduled_jobs",
    ):
        assert expected in tables, f"{expected} missing from the migrated schema"
    assert "school_settings" not in tables, "superseded by schools"


def test_the_migrated_schema_accepts_the_seed(migrated_db):
    """The check that would have caught the dropped server_default."""
    result = _run([sys.executable, "seed.py"], migrated_db)
    assert result.returncode == 0, result.stderr[-3000:]


def test_a_worker_runs_against_the_migrated_schema(migrated_db):
    """Scheduler and worker, with no HTTP request involved anywhere."""
    seeded = _run([sys.executable, "seed.py"], migrated_db)
    assert seeded.returncode == 0, seeded.stderr[-2000:]

    result = _run([sys.executable, "worker.py", "--once"], migrated_db)
    assert result.returncode == 0, result.stderr[-3000:]
    assert "done" in result.stderr or "done" in result.stdout
