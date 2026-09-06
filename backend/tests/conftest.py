"""Test fixtures: a fresh seeded schema per session, plus a token per role."""

import os
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.db import Base, get_db, make_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import ClassSection, Student, Subject, Teacher, User  # noqa: E402
from seed import seed  # noqa: E402

TEST_URL = os.environ.get("TEST_DATABASE_URL") or settings.TEST_DATABASE_URL


@pytest.fixture(scope="session")
def engine():
    url = TEST_URL
    if url.startswith("sqlite"):
        path = Path(url.replace("sqlite:///", ""))
        if path.exists():
            path.unlink()
    eng = make_engine(url)
    if url.startswith("sqlite"):
        # pysqlite does not emit BEGIN on its own, which breaks the SAVEPOINT
        # rollback the per-test transaction relies on. Documented workaround:
        # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#serializable-isolation
        from sqlalchemy import event

        @event.listens_for(eng, "connect")
        def _no_implicit_begin(dbapi_conn, _record):
            dbapi_conn.isolation_level = None

        @event.listens_for(eng, "begin")
        def _explicit_begin(conn):
            conn.exec_driver_sql("BEGIN")

    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def _seeded_once(engine):
    """Seed exactly once: bcrypt hashing 53 accounts is far too slow per test."""
    with sessionmaker(bind=engine)() as db:
        seed(db)


@pytest.fixture()
def connection(engine, _seeded_once):
    """Each test runs inside a transaction that is rolled back afterwards, so
    writes in one test are invisible to the next."""
    conn = engine.connect()
    trans = conn.begin()
    yield conn
    trans.rollback()
    conn.close()


@pytest.fixture()
def db(connection):
    """One session shared by the test body and the app, so both see the same
    uncommitted state inside the test transaction."""
    session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    def override():
        yield db

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _token(client, role: str, login_id: str, password: str) -> str:
    r = client.post(
        "/auth/login", json={"role": role, "login_id": login_id, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin(client):
    return auth(_token(client, "admin", "admin@sunrisepublic.edu", "Admin@123"))


@pytest.fixture()
def teacher(client):
    """TCH001 — class teacher of 10-A and its Mathematics teacher."""
    return auth(_token(client, "teacher", "TCH001", "Teacher@123"))


@pytest.fixture()
def other_teacher(client):
    """TCH004 — deliberately teaches neither 10-A nor its Mathematics."""
    return auth(_token(client, "teacher", "TCH004", "Teacher@123"))


def _login_id_in(db, class_name: str, roll_no: int = 1) -> str:
    """Resolve a student login by where they sit rather than by a literal
    admission number: those are now allocated from a sequence, so hard-coding
    one would tie the tests to seed ordering."""
    from app.models import ClassSection, Enrolment, Student, User

    return db.scalar(
        select(User.login_id)
        .join(Student, Student.user_id == User.id)
        .join(Enrolment, Enrolment.student_id == Student.id)
        .join(ClassSection, ClassSection.id == Enrolment.class_section_id)
        .where(ClassSection.class_name == class_name, Enrolment.roll_no == roll_no)
    )


@pytest.fixture()
def student(client, db):
    """Roll 1 of 10-A."""
    return auth(_token(client, "student", _login_id_in(db, "10"), "Student@123"))


@pytest.fixture()
def other_student(client, db):
    """Roll 1 of 8-A — a different section, so scoping is a real boundary."""
    return auth(_token(client, "student", _login_id_in(db, "8"), "Student@123"))


@pytest.fixture()
def parent(client):
    return auth(_token(client, "parent", "9876500001", "Parent@123"))


@pytest.fixture()
def other_parent(client):
    return auth(_token(client, "parent", "9876500010", "Parent@123"))


@pytest.fixture()
def ids(db):
    """Handy primary keys used across the suite."""
    section_10a = db.scalar(select(ClassSection).where(ClassSection.class_name == "10"))
    section_9a = db.scalar(select(ClassSection).where(ClassSection.class_name == "9"))
    section_8a = db.scalar(select(ClassSection).where(ClassSection.class_name == "8"))
    maths = db.scalar(select(Subject).where(Subject.code == "MAT"))
    hindi = db.scalar(select(Subject).where(Subject.code == "HIN"))
    from app.models import Enrolment

    def student_in(class_name, roll_no=1):
        return db.scalar(
            select(Student)
            .join(Enrolment, Enrolment.student_id == Student.id)
            .join(ClassSection, ClassSection.id == Enrolment.class_section_id)
            .where(ClassSection.class_name == class_name, Enrolment.roll_no == roll_no)
        )

    s1 = student_in("10")
    s17 = student_in("8")
    tch1 = db.scalar(select(Teacher).join(User).where(User.login_id == "TCH001"))
    return {
        "section_10a": section_10a.id,
        "section_9a": section_9a.id,
        "section_8a": section_8a.id,
        "maths": maths.id,
        "hindi": hindi.id,
        "student_1": s1.id,
        "student_17": s17.id,
        "teacher_1": tch1.id,
    }
