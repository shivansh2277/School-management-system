"""The report library, viewer and export centre (ERP_BLUEPRINT section 5.10.3).

Three endpoints for twenty-one reports, because the reports differ in their
parameters and their permission rather than in their plumbing, and a route each
would be twenty-one places to forget the gate. The permission is still checked
at the route - it is just read from the registry once the caller has said which
report they want, rather than baked into a decorator per handler.

There is deliberately no ad-hoc or custom report builder here. A query builder
behind a records clerk's screen is the injection surface section 3.16 already
refused a `formula` calculation method over, and the parameters a report takes
are declared in the registry precisely so that nothing else can be passed.
"""

import csv
import io
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.report_registry import CATEGORIES
from app.models import User
from app.services import audit
from app.services import reports as svc
from app.services.rbac import Authz, get_authz
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/reports",
    tags=["reports"],
    dependencies=[Depends(module_enabled("reports"))],
)


def _params(request: Request) -> dict:
    """Whatever the caller sent, for the registry to accept or refuse.

    Taken raw rather than declared per report, and validated in
    `reports._coerce()` against the parameters that report actually declares -
    so an unknown parameter is a 422 naming the ones that exist, not a value
    silently ignored.
    """
    return dict(request.query_params)


@router.get("")
def library(
    user: User = Depends(get_current_user),
    authz: Authz = Depends(get_authz),
    db: Session = Depends(get_db),
) -> dict:
    """The Report Library of section 5.10.3, by category."""
    return {"categories": CATEGORIES, "reports": svc.available(db, user, authz)}


@router.get("/{code}")
def run(
    code: str,
    request: Request,
    user: User = Depends(get_current_user),
    authz: Authz = Depends(get_authz),
    db: Session = Depends(get_db),
) -> dict:
    """Run one report. Permission and scope are `reports._authorise()`."""
    return svc.run(db, user, authz, code, _params(request))


@router.get("/{code}/export")
def export(
    code: str,
    request: Request,
    user: User = Depends(get_current_user),
    authz: Authz = Depends(get_authz),
    db: Session = Depends(get_db),
) -> Response:
    """The same report as a CSV, audited.

    The download runs the identical `svc.run()` the screen does - not a second
    query built for the file - so the two cannot show different rows. Section
    5.10.9's audit applies to every export, not only the student roster: a
    defaulter list is a list of families and what they owe, which is personal
    data by any reading.

    A GET that commits, deliberately, for the reason given on the student
    export: the audit row is the requirement, not a side effect of a read.
    """
    result = svc.run(db, user, authz, code, _params(request))
    data = result["data"]
    rows = data if isinstance(data, list) else [data]

    buf = io.StringIO(newline="")
    meta = result["meta"]
    stated = ", ".join(f"{k}={v}" for k, v in meta["filters"].items()) or "none"
    print(
        f"# {result['report']['name']} | academic year {meta['academic_year']}"
        f" | filters: {stated}"
        f" | generated {meta['generated_at']} by {meta['generated_by']}",
        file=buf,
    )
    if rows:
        # A report whose rows are dicts writes as a table. One that answers with
        # a single figure - a ratio, an attendance summary - writes as its one
        # row, which is what it is.
        columns = list(dict.fromkeys(k for r in rows if isinstance(r, dict) for k in r))
        writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(r for r in rows if isinstance(r, dict))

    audit.record_export(
        db,
        actor=user,
        school_id=user.school_id,
        what=f"report:{code}",
        rows=len(rows),
        filters=meta["filters"],
    )
    db.commit()

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{code}-{datetime.now(UTC):%Y%m%d}.csv"'
            )
        },
    )
