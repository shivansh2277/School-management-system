"""audit defect remediations: student dossier fields and timetable constraints & publication lifecycle

Revision ID: a2b3c4d5e6f0
Revises: a1b2c3d4e5f9
Create Date: 2026-10-29 21:58:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f0'
down_revision: Union[str, None] = 'a1b2c3d4e5f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add dossier fields to students table using batch_alter_table for SQLite compatibility
    with op.batch_alter_table('students') as batch_op:
        batch_op.add_column(sa.Column('blood_group', sa.String(10), nullable=True))
        batch_op.add_column(sa.Column('nationality', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('religion', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('caste_category', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('mother_tongue', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('place_of_birth', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('identification_marks', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('is_single_child', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        batch_op.add_column(sa.Column('aadhaar_last4', sa.String(4), nullable=True))
        batch_op.add_column(sa.Column('aadhaar_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        batch_op.add_column(sa.Column('emergency_doctor', sa.String(120), nullable=True))
        batch_op.add_column(sa.Column('emergency_doctor_phone', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('known_allergies', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('chronic_conditions', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('regular_medications', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('previous_school', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('application_id', sa.BigInteger(), sa.ForeignKey('applications.id', name='fk_students_application_id'), nullable=True))

    # 2. Add is_published and unique constraints to timetable_slots
    with op.batch_alter_table('timetable_slots') as batch_op:
        batch_op.add_column(sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        batch_op.create_unique_constraint('uq_timetable_teacher_slot', ['teacher_id', 'day_of_week', 'period_id'])

    # Backfill existing slots as published so existing seeded timetables remain visible
    op.execute("UPDATE timetable_slots SET is_published = true WHERE is_published = false;")

    # 3. Add partial unique index on room slot (normalized uppercase and trimmed)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_timetable_room_slot ON timetable_slots (school_id, UPPER(TRIM(room)), day_of_week, period_id) "
        "WHERE room IS NOT NULL AND TRIM(room) != '';"
    )


def downgrade() -> None:
    # 1. Drop timetable constraints and index
    op.execute("DROP INDEX IF EXISTS uq_timetable_room_slot;")
    with op.batch_alter_table('timetable_slots') as batch_op:
        batch_op.drop_constraint('uq_timetable_teacher_slot', type_='unique')
        batch_op.drop_column('is_published')

    # 2. Drop students columns
    with op.batch_alter_table('students') as batch_op:
        batch_op.drop_column('application_id')
        batch_op.drop_column('previous_school')
        batch_op.drop_column('regular_medications')
        batch_op.drop_column('chronic_conditions')
        batch_op.drop_column('known_allergies')
        batch_op.drop_column('emergency_doctor_phone')
        batch_op.drop_column('emergency_doctor')
        batch_op.drop_column('aadhaar_verified')
        batch_op.drop_column('aadhaar_last4')
        batch_op.drop_column('is_single_child')
        batch_op.drop_column('identification_marks')
        batch_op.drop_column('place_of_birth')
        batch_op.drop_column('mother_tongue')
        batch_op.drop_column('caste_category')
        batch_op.drop_column('religion')
        batch_op.drop_column('nationality')
        batch_op.drop_column('blood_group')
