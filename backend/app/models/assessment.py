from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantBase


class AssessmentScheme(TenantBase):
    """The shape of a year's assessment: its terms and what each is marked out
    of (§5.4.3).

    CBSE marks a subject four ways in a term — a periodic test, the notebook,
    subject enrichment and the term examination — and the report card prints
    all four with a total. Without a scheme the system can only hold one number
    per subject per exam, which is the v0 model and cannot produce that card.

    The scheme is data, not code (§0.5, §0.15): a school that marks out of
    different numbers, or runs three terms, changes rows.
    """

    __tablename__ = "assessment_schemes"
    __table_args__ = (
        UniqueConstraint(
            "academic_year_id", "name", name="uq_assessment_scheme_name"
        ),
        # One scheme in force per year. A second one would make "what is this
        # subject out of" ambiguous halfway through a term.
        Index(
            "uq_assessment_scheme_active",
            "academic_year_id",
            unique=True,
            postgresql_where=text("is_active"),
            sqlite_where=text("is_active"),
        ),
    )

    academic_year_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("academic_years.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class SchemeComponent(TenantBase):
    """One markable column of the report card: "Term 1, Periodic Test, out of 10"."""

    __tablename__ = "scheme_components"
    __table_args__ = (
        UniqueConstraint("scheme_id", "term", "code", name="uq_scheme_component"),
        CheckConstraint("max_marks > 0", name="ck_scheme_component_max_marks"),
    )

    scheme_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("assessment_schemes.id"), nullable=False, index=True
    )
    term: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(12), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    # Print order on the report card, which is not alphabetical and not the
    # order somebody happened to type them in.
    sequence: Mapped[int] = mapped_column(nullable=False, default=0)

    scheme = relationship("AssessmentScheme", lazy="joined")


class Exam(TenantBase):
    """One assessment event: "Term 1 Periodic Test", "Term 1 Examination".

    An exam that cites a scheme component is a column of the report card. One
    that does not is an ordinary class test — it is marked and readable, and it
    simply does not print. Keeping that nullable is what lets a school run a
    surprise test without first amending its assessment scheme.
    """

    __tablename__ = "exams"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    term: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheme_component_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("scheme_components.id"), index=True
    )

    component = relationship("SchemeComponent", lazy="joined")


class ExamSchedule(TenantBase):
    """One paper: this exam, this section, this subject.

    The marks lock lives here rather than on each mark, because §5.4.7 locks
    *marks entry per subject* — the paper is what an exam controller closes,
    and a per-mark lock would let a paper be half shut.
    """

    __tablename__ = "exam_schedule"
    __table_args__ = (
        UniqueConstraint("exam_id", "class_section_id", "subject_id", name="uq_exam_schedule"),
    )

    exam_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exams.id"), nullable=False)
    class_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("class_sections.id"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    room: Mapped[str | None] = mapped_column(String(20))

    # Set when the exam controller closes entry. After this a mark can still be
    # changed, but only with the override permission and a reason, and the
    # change is audited without exception (§5.4.9).
    marks_locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    marks_locked_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id")
    )

    @property
    def is_locked(self) -> bool:
        return self.marks_locked_at is not None


class Mark(TenantBase):
    """One child's result on one paper.

    **Absent, exempted and zero are three different things** (§5.4.9), and a
    single nullable number cannot say which. A zero is a mark: the child sat
    the paper and scored nothing. An absence is not a mark, and neither is an
    exemption — a child excused from a paper should not be averaged against it.
    So `marks_obtained` is nullable and the two flags say which of the three a
    null means.
    """

    __tablename__ = "marks"
    __table_args__ = (
        UniqueConstraint("exam_schedule_id", "student_id", name="uq_mark"),
        CheckConstraint("marks_obtained >= 0", name="ck_marks_non_negative"),
        # A child is absent or exempted, not both, and neither carries a score.
        CheckConstraint(
            "NOT (is_absent AND is_exempted)", name="ck_mark_absent_xor_exempted"
        ),
        CheckConstraint(
            "(is_absent OR is_exempted) = (marks_obtained IS NULL)",
            name="ck_mark_score_matches_state",
        ),
    )

    exam_schedule_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("exam_schedule.id"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("students.id"), nullable=False)
    marks_obtained: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    is_absent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_exempted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    remarks: Mapped[str | None] = mapped_column(String(200))
    # The actor is a user, not an employee. An exam controller entering a
    # correction may hold no teaching post, and every other actor in this
    # codebase — the audit log included — is identified by user.
    entered_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )


class GradeBand(TenantBase):
    """One row of a grading scale: "91 and above is an A1"."""

    __tablename__ = "grade_bands"
    __table_args__ = (
        UniqueConstraint("grading_scale_id", "grade", name="uq_grade_band_grade"),
        UniqueConstraint("grading_scale_id", "min_percent", name="uq_grade_band_floor"),
        CheckConstraint(
            "min_percent >= 0 AND min_percent <= 100", name="ck_grade_band_percent"
        ),
    )

    grading_scale_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("grading_scales.id"), nullable=False, index=True
    )
    min_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    grade: Mapped[str] = mapped_column(String(4), nullable=False)
    # "Outstanding", "Needs improvement" — CBSE prints the word, not the code.
    description: Mapped[str | None] = mapped_column(String(40))

    scale = relationship("GradingScale", lazy="joined")


class GradingScale(TenantBase):
    """A named set of grade bands, versioned.

    §0.8 freezes a published report card by snapshotting the grade *and the
    scale version used*. That is only expressible if the scale is a row a
    publication can point at: with bands hanging directly off the school, an
    edit to a band silently re-graded every card ever issued.

    A school edits bands freely until a card is published against the scale;
    after that the edit becomes a new version, and the old one stays readable
    for the documents that cite it.
    """

    __tablename__ = "grading_scales"
    __table_args__ = (
        UniqueConstraint("school_id", "name", "version", name="uq_grading_scale_version"),
        # One scale in force per school, enforced by the database rather than
        # by whoever remembers to deactivate the previous one.
        Index(
            "uq_grading_scale_active",
            "school_id",
            unique=True,
            postgresql_where=text("is_active"),
            sqlite_where=text("is_active"),
        ),
    )

    name: Mapped[str] = mapped_column(String(60), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Set when the first report card cites this version. From then on the bands
    # are history, not configuration.
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ReportCardPublication(TenantBase):
    """A published report card: frozen, numbered, and citing its own rules.

    §0.8 makes a published card a *document*, not a view. Reopening it months
    later must show exactly what was issued, even if a grade band has been
    edited since — so the whole card is stored as it was rendered, and the
    grading scale and assessment scheme it was computed against are cited by id
    rather than re-resolved on read.

    This supersedes BLUEPRINT §7.5 for published documents only: live screens
    keep computing from `grade_bands`, which is why the two paths exist side by
    side rather than one replacing the other.
    """

    __tablename__ = "report_card_publications"
    __table_args__ = (
        # One published card per child per term. A correction is a new version
        # of the document, not an edit to this row.
        UniqueConstraint("enrolment_id", "term", name="uq_report_card_term"),
    )

    enrolment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enrolments.id"), nullable=False, index=True
    )
    term: Mapped[str] = mapped_column(String(20), nullable=False)
    scheme_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("assessment_schemes.id"), nullable=False
    )
    grading_scale_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("grading_scales.id"), nullable=False
    )
    # The document number, from the same gapless sequence machinery receipts
    # and admission numbers use.
    document_no: Mapped[str] = mapped_column(String(32), nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    published_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))

    result_status: Mapped[str] = mapped_column(String(20), nullable=False)
    # The card exactly as issued. Storing the rendered document rather than
    # recomputing it is the whole freeze: nothing downstream of publication can
    # move a number on a card a parent has already been shown.
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
