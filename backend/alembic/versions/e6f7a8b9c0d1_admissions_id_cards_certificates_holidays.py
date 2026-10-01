"""admissions documents, apaar, certificates, holidays, library

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-10-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e6f7a8b9c0d1"
down_revision: str | None = "d5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1. applications table — APAAR fields
    app_cols = [c["name"] for c in insp.get_columns("applications")]
    if "apaar_id" not in app_cols:
        op.add_column("applications", sa.Column("apaar_id", sa.String(12), nullable=True))
    if "apaar_consent" not in app_cols:
        op.add_column(
            "applications",
            sa.Column("apaar_consent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
    if "apaar_consent_guardian_name" not in app_cols:
        op.add_column(
            "applications",
            sa.Column("apaar_consent_guardian_name", sa.String(120), nullable=True),
        )
    if "apaar_consent_guardian_relation" not in app_cols:
        op.add_column(
            "applications",
            sa.Column("apaar_consent_guardian_relation", sa.String(40), nullable=True),
        )
    if "apaar_consent_at" not in app_cols:
        op.add_column(
            "applications",
            sa.Column("apaar_consent_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 2. students table — APAAR fields
    student_cols = [c["name"] for c in insp.get_columns("students")]
    if "apaar_id" not in student_cols:
        op.add_column("students", sa.Column("apaar_id", sa.String(12), nullable=True))
        op.create_index("ix_students_apaar_id", "students", ["apaar_id"])
    if "apaar_consent" not in student_cols:
        op.add_column(
            "students",
            sa.Column("apaar_consent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
    if "apaar_consent_guardian_name" not in student_cols:
        op.add_column(
            "students",
            sa.Column("apaar_consent_guardian_name", sa.String(120), nullable=True),
        )
    if "apaar_consent_guardian_relation" not in student_cols:
        op.add_column(
            "students",
            sa.Column("apaar_consent_guardian_relation", sa.String(40), nullable=True),
        )
    if "apaar_consent_at" not in student_cols:
        op.add_column(
            "students",
            sa.Column("apaar_consent_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 3. application_document_overrides table
    if not insp.has_table("application_document_overrides"):
        op.create_table(
            "application_document_overrides",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, primary_key=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("application_id", sa.BigInteger(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
            sa.Column("document_code", sa.String(40), nullable=False),
            sa.Column("authorized_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("application_id", "document_code", name="uq_app_doc_override"),
        )
        op.create_index("ix_app_doc_override", "application_document_overrides", ["application_id", "document_code"])
        op.create_index("ix_app_doc_override_school", "application_document_overrides", ["school_id"])

    # 4. holidays table upgrade & backfill
    holiday_cols = [c["name"] for c in insp.get_columns("holidays")]
    with op.batch_alter_table("holidays") as batch_op:
        if "start_date" not in holiday_cols:
            batch_op.add_column(sa.Column("start_date", sa.Date(), nullable=True))
        if "end_date" not in holiday_cols:
            batch_op.add_column(sa.Column("end_date", sa.Date(), nullable=True))
        if "description" not in holiday_cols:
            batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        if "is_school_wide" not in holiday_cols:
            batch_op.add_column(sa.Column("is_school_wide", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        if "status" not in holiday_cols:
            batch_op.add_column(sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'active'")))
        if "created_by_id" not in holiday_cols:
            batch_op.add_column(sa.Column("created_by_id", sa.BigInteger(), nullable=True))
        if "cancelled_by_id" not in holiday_cols:
            batch_op.add_column(sa.Column("cancelled_by_id", sa.BigInteger(), nullable=True))
        if "cancellation_reason" not in holiday_cols:
            batch_op.add_column(sa.Column("cancellation_reason", sa.Text(), nullable=True))

    # Backfill start_date and end_date from existing date column
    bind.execute(sa.text("""
        UPDATE holidays
        SET start_date = date,
            end_date = date,
            is_school_wide = TRUE,
            status = 'active'
        WHERE start_date IS NULL;
    """))

    if bind.dialect.name != "sqlite":
        op.alter_column("holidays", "start_date", nullable=False)
        op.alter_column("holidays", "end_date", nullable=False)

    # 5. holiday_class_sections table
    if not insp.has_table("holiday_class_sections"):
        op.create_table(
            "holiday_class_sections",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, primary_key=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("holiday_id", sa.BigInteger(), sa.ForeignKey("holidays.id", ondelete="CASCADE"), nullable=False),
            sa.Column("class_section_id", sa.BigInteger(), sa.ForeignKey("class_sections.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("holiday_id", "class_section_id", name="uq_holiday_class_section"),
        )
        op.create_index("ix_holiday_class_sections_school", "holiday_class_sections", ["school_id"])

    # 6. certificate_templates table
    if not insp.has_table("certificate_templates"):
        op.create_table(
            "certificate_templates",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, primary_key=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("certificate_type", sa.String(30), nullable=False),
            sa.Column("title", sa.String(120), nullable=False),
            sa.Column("header_text", sa.Text(), nullable=True),
            sa.Column("body_template", sa.Text(), nullable=False),
            sa.Column("signatory_name", sa.String(120), nullable=True),
            sa.Column("signatory_title", sa.String(80), server_default="Principal", nullable=True),
            sa.Column("show_seal", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("school_id", "certificate_type", name="uq_school_cert_template"),
        )
        op.create_index("ix_cert_templates_school", "certificate_templates", ["school_id"])

    # 7. student_certificates table
    if not insp.has_table("student_certificates"):
        op.create_table(
            "student_certificates",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, primary_key=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("certificate_type", sa.String(30), nullable=False),
            sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
            sa.Column("enrolment_id", sa.BigInteger(), sa.ForeignKey("enrolments.id"), nullable=False),
            sa.Column("certificate_no", sa.String(40), nullable=True),
            sa.Column("issue_date", sa.Date(), nullable=True),
            sa.Column("issued_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(20), server_default="requested", nullable=False),
            sa.Column("requested_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("requested_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_by_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("data_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("is_reissue", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("reissue_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
            sa.Column("reissue_reason", sa.Text(), nullable=True),
            sa.Column("original_certificate_id", sa.BigInteger(), sa.ForeignKey("student_certificates.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("school_id", "certificate_no", name="uq_school_certificate_no"),
        )
        op.create_index("ix_cert_student", "student_certificates", ["school_id", "student_id"])
        op.create_index("ix_cert_type", "student_certificates", ["school_id", "certificate_type"])

    # 8. books table
    if not insp.has_table("books"):
        op.create_table(
            "books",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, primary_key=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("isbn", sa.String(20), nullable=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("author", sa.String(120), nullable=False),
            sa.Column("publisher", sa.String(120), nullable=True),
            sa.Column("category", sa.String(60), server_default="General", nullable=False),
            sa.Column("total_copies", sa.Integer(), server_default=sa.text("1"), nullable=False),
            sa.Column("available_copies", sa.Integer(), server_default=sa.text("1"), nullable=False),
            sa.Column("shelf_location", sa.String(40), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_books_title", "books", ["school_id", "title"])
        op.create_index("ix_books_category", "books", ["school_id", "category"])
        op.create_index("ix_books_isbn", "books", ["isbn"])

    # 9. book_copies table
    if not insp.has_table("book_copies"):
        op.create_table(
            "book_copies",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, primary_key=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("book_id", sa.BigInteger(), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
            sa.Column("accession_no", sa.String(40), nullable=False),
            sa.Column("barcode", sa.String(60), nullable=True),
            sa.Column("status", sa.String(20), server_default="available", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("school_id", "accession_no", name="uq_book_copy_accession"),
        )
        op.create_index("ix_book_copies_school_book", "book_copies", ["school_id", "book_id"])

    # 10. library_loans table
    if not insp.has_table("library_loans"):
        op.create_table(
            "library_loans",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, primary_key=True),
            sa.Column("school_id", sa.BigInteger(), sa.ForeignKey("schools.id"), nullable=False),
            sa.Column("book_copy_id", sa.BigInteger(), sa.ForeignKey("book_copies.id"), nullable=False),
            sa.Column("enrolment_id", sa.BigInteger(), sa.ForeignKey("enrolments.id"), nullable=True),
            sa.Column("employee_id", sa.BigInteger(), sa.ForeignKey("employees.id"), nullable=True),
            sa.Column("issued_by_id", sa.BigInteger(), sa.ForeignKey("employees.id"), nullable=False),
            sa.Column("issued_on", sa.Date(), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=False),
            sa.Column("returned_on", sa.Date(), nullable=True),
            sa.Column("status", sa.String(20), server_default="active", nullable=False),
            sa.Column("fine_amount", sa.Numeric(10, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("fine_paid", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("renewal_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
            sa.Column("remarks", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_loan_enrolment", "library_loans", ["school_id", "enrolment_id", "status"])
        op.create_index("ix_loan_employee", "library_loans", ["school_id", "employee_id", "status"])
        op.create_index("ix_loan_due_date", "library_loans", ["school_id", "due_date", "status"])


def downgrade() -> None:
    op.drop_table("library_loans")
    op.drop_table("book_copies")
    op.drop_table("books")
    op.drop_table("student_certificates")
    op.drop_table("certificate_templates")
    op.drop_table("holiday_class_sections")

    op.drop_column("holidays", "cancellation_reason")
    op.drop_column("holidays", "cancelled_by_id")
    op.drop_column("holidays", "created_by_id")
    op.drop_column("holidays", "status")
    op.drop_column("holidays", "is_school_wide")
    op.drop_column("holidays", "description")
    op.drop_column("holidays", "end_date")
    op.drop_column("holidays", "start_date")

    op.drop_table("application_document_overrides")

    op.drop_index("ix_students_apaar_id", "students")
    op.drop_column("students", "apaar_consent_at")
    op.drop_column("students", "apaar_consent_guardian_relation")
    op.drop_column("students", "apaar_consent_guardian_name")
    op.drop_column("students", "apaar_consent")
    op.drop_column("students", "apaar_id")

    op.drop_column("applications", "apaar_consent_at")
    op.drop_column("applications", "apaar_consent_guardian_relation")
    op.drop_column("applications", "apaar_consent_guardian_name")
    op.drop_column("applications", "apaar_consent")
    op.drop_column("applications", "apaar_id")
