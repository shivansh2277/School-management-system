from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.rbac import require_permission
from app.models import Homework, User, UserRole
from app.schemas.common import HomeworkCreate, HomeworkOut, HomeworkUpdate, SubmissionRow
from app.services import homework as svc
from app.services import scoping

router = APIRouter(prefix="/teacher", tags=["teacher"])
teacher_only = require_permission("homework.item.read")


@router.get("/homework", response_model=list[HomeworkOut])
def list_homework(
    class_section_id: int | None = None,
    subject_id: int | None = None,
    user: User = Depends(teacher_only),
    db: Session = Depends(get_db),
) -> list[HomeworkOut]:
    me = scoping.teacher_for(db, user)
    q = select(Homework).where(Homework.teacher_id == me.id)
    if class_section_id is not None:
        q = q.where(Homework.class_section_id == class_section_id)
    if subject_id is not None:
        q = q.where(Homework.subject_id == subject_id)
    return svc.to_out(db, list(db.scalars(q.order_by(Homework.due_date.desc()))))


@router.post("/homework", response_model=HomeworkOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("homework.item.write"))])
def create(
    body: HomeworkCreate, user: User = Depends(teacher_only), db: Session = Depends(get_db)
) -> HomeworkOut:
    return svc.create(db, user, body)


@router.patch("/homework/{homework_id}", response_model=HomeworkOut, dependencies=[Depends(require_permission("homework.item.write"))])
def update(
    homework_id: int,
    body: HomeworkUpdate,
    user: User = Depends(teacher_only),
    db: Session = Depends(get_db),
) -> HomeworkOut:
    return svc.update(db, user, homework_id, body)


@router.delete("/homework/{homework_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("homework.item.write"))])
def delete(
    homework_id: int, user: User = Depends(teacher_only), db: Session = Depends(get_db)
) -> Response:
    svc.delete(db, user, homework_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/homework/{homework_id}/submissions", response_model=list[SubmissionRow])
def submissions(
    homework_id: int, user: User = Depends(teacher_only), db: Session = Depends(get_db)
) -> list[SubmissionRow]:
    return svc.submissions(db, user, homework_id)
