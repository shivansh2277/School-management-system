"""Fee head, plan, assignment and concession setup (ERP_BLUEPRINT §5.5.3
screens 2-5). The counter, invoices and reports live in `fees.py`."""

from datetime import date as Date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import (
    ConcessionStatus,
    ConcessionType,
    Enrolment,
    FeeConcession,
    FeeFrequency,
    FeeHead,
    FeeHeadType,
    FeePlan,
    FeePlanItem,
    StudentFeePlan,
    User,
)
from app.services import fee_setup as svc
from app.services.common import class_sort_key
from app.services.rbac import require_permission
from app.services.school_settings import module_enabled

router = APIRouter(
    prefix="/admin/fees",
    tags=["fees"],
    dependencies=[Depends(module_enabled("fees"))],
)

reader = require_permission("fees.invoice.read", school_wide=True)
setup = Depends(require_permission("fees.setup.manage"))
approver = require_permission("fees.concession.approve", school_wide=True)


class HeadIn(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    code: str
    type: FeeHeadType = FeeHeadType.recurring
    is_refundable: bool = False
    gl_code: str | None = None
    is_active: bool = True


class PlanItemIn(BaseModel):
    model_config = {"extra": "forbid"}

    fee_head_id: int
    amount: Decimal
    frequency: FeeFrequency = FeeFrequency.monthly


class PlanIn(BaseModel):
    model_config = {"extra": "forbid"}

    academic_year_id: int
    name: str
    class_name: str | None = None
    items: list[PlanItemIn] = []


class AssignIn(BaseModel):
    model_config = {"extra": "forbid"}

    enrolment_id: int
    fee_plan_id: int


class ConcessionIn(BaseModel):
    model_config = {"extra": "forbid"}

    enrolment_id: int
    type: ConcessionType
    reason: str
    fee_head_id: int | None = None
    percent: Decimal | None = None
    amount: Decimal | None = None
    valid_from: Date | None = None
    valid_to: Date | None = None


class DecideIn(BaseModel):
    model_config = {"extra": "forbid"}

    approve: bool
    reason: str | None = None


def _head_out(h: FeeHead) -> dict:
    return {
        "id": h.id,
        "name": h.name,
        "code": h.code,
        "type": h.type,
        "is_refundable": h.is_refundable,
        "gl_code": h.gl_code,
        "is_active": h.is_active,
    }


def _plan_out(p: FeePlan) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "class_name": p.class_name,
        "academic_year_id": p.academic_year_id,
        "is_active": p.is_active,
        "items": [
            {
                "id": i.id,
                "fee_head_id": i.fee_head_id,
                "fee_head": i.head.name,
                "amount": i.amount,
                "frequency": i.frequency,
            }
            for i in p.items
        ],
        "monthly_total": sum(
            (i.amount for i in p.items if i.frequency is FeeFrequency.monthly), Decimal(0)
        ),
    }


def _concession_out(c: FeeConcession) -> dict:
    return {
        "id": c.id,
        "enrolment_id": c.enrolment_id,
        "type": c.type,
        "fee_head_id": c.fee_head_id,
        "percent": c.percent,
        "amount": c.amount,
        "reason": c.reason,
        "status": c.status,
        "approved_by": c.approved_by,
        "valid_from": c.valid_from,
        "valid_to": c.valid_to,
    }


@router.get("/heads")
def heads(user: User = Depends(reader), db: Session = Depends(get_db)) -> list[dict]:
    return [
        _head_out(h)
        for h in db.scalars(
            select(FeeHead).where(FeeHead.school_id == user.school_id).order_by(FeeHead.code)
        )
    ]


@router.post("/heads", status_code=201, dependencies=[setup])
def create_head(
    body: HeadIn, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    if db.scalar(
        select(FeeHead).where(FeeHead.school_id == user.school_id, FeeHead.code == body.code)
    ):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Fee head {body.code} already exists")
    head = FeeHead(school_id=user.school_id, **body.model_dump())
    db.add(head)
    db.commit()
    return _head_out(head)


@router.get("/plans")
def plans(
    academic_year_id: int | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = select(FeePlan).where(FeePlan.school_id == user.school_id)
    if academic_year_id is not None:
        q = q.where(FeePlan.academic_year_id == academic_year_id)
    # Sorted here, not in SQL: class_name is a String, so the database orders
    # "1", "10", "2" and the fee structure on Settings listed class 10 second.
    rows = sorted(
        db.scalars(q), key=lambda p: (*class_sort_key(p.class_name), p.name)
    )
    return [_plan_out(p) for p in rows]


@router.post("/plans", status_code=201, dependencies=[setup])
def create_plan(
    body: PlanIn, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    owned = set(db.scalars(select(FeeHead.id).where(FeeHead.school_id == user.school_id)))
    for item in body.items:
        if item.fee_head_id not in owned:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"Unknown fee head {item.fee_head_id}"
            )
    plan = FeePlan(
        school_id=user.school_id,
        academic_year_id=body.academic_year_id,
        name=body.name,
        class_name=body.class_name,
        items=[
            FeePlanItem(school_id=user.school_id, **item.model_dump()) for item in body.items
        ],
    )
    db.add(plan)
    db.commit()
    return _plan_out(plan)


@router.post("/assignments", status_code=201, dependencies=[setup])
def assign_plan(
    body: AssignIn, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    enrolment = db.get(Enrolment, body.enrolment_id)
    plan = db.get(FeePlan, body.fee_plan_id)
    if enrolment is None or enrolment.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enrolment not found")
    if plan is None or plan.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fee plan not found")
    row = db.scalar(select(StudentFeePlan).where(StudentFeePlan.enrolment_id == enrolment.id))
    if row is None:
        row = StudentFeePlan(
            school_id=user.school_id, enrolment_id=enrolment.id, fee_plan_id=plan.id
        )
        db.add(row)
    else:
        row.fee_plan_id = plan.id
    row.assigned_by = user.id
    db.commit()
    return {"enrolment_id": enrolment.id, "fee_plan_id": plan.id}


@router.get("/concessions")
def concessions(
    status_: ConcessionStatus | None = None,
    user: User = Depends(reader),
    db: Session = Depends(get_db),
) -> list[dict]:
    q = select(FeeConcession).where(FeeConcession.school_id == user.school_id)
    if status_ is not None:
        q = q.where(FeeConcession.status == status_)
    return [_concession_out(c) for c in db.scalars(q.order_by(FeeConcession.id))]


@router.post("/concessions", status_code=201, dependencies=[setup])
def request_concession(
    body: ConcessionIn, user: User = Depends(reader), db: Session = Depends(get_db)
) -> dict:
    if (body.percent is None) == (body.amount is None):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Give either a percent or an amount, not both",
        )
    enrolment = db.get(Enrolment, body.enrolment_id)
    if enrolment is None or enrolment.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enrolment not found")
    row = FeeConcession(school_id=user.school_id, requested_by=user.id, **body.model_dump())
    db.add(row)
    db.commit()
    return _concession_out(row)


@router.post("/concessions/{concession_id}/decide")
def decide_concession(
    concession_id: int,
    body: DecideIn,
    user: User = Depends(approver),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(FeeConcession, concession_id)
    if row is None or row.school_id != user.school_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Concession not found")
    return _concession_out(svc.decide(db, row, user, body.approve, body.reason))


@router.post("/concessions/sibling-sweep", dependencies=[setup])
def sibling_sweep(user: User = Depends(reader), db: Session = Depends(get_db)) -> dict:
    """Grant the §0.6 sibling concession to every family that qualifies.

    Idempotent, so it is safe to run after any admission intake rather than
    remembering which families are new.
    """
    return svc.apply_sibling_concessions(db, user.school_id, actor=user)
