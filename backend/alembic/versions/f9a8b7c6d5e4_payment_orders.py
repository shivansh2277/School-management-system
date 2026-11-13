"""payment orders for direct upi and razorpay

Revision ID: f9a8b7c6d5e4
Revises: e9f8a7b6c5d4
Create Date: 2026-11-07 00:50:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9a8b7c6d5e4'
down_revision: Union[str, None] = 'e9f8a7b6c5d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payment_orders',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('school_id', sa.BigInteger(), nullable=False),
        sa.Column('order_no', sa.String(length=40), nullable=False),
        sa.Column('enrolment_id', sa.BigInteger(), nullable=False),
        sa.Column('student_id', sa.BigInteger(), nullable=False),
        sa.Column('invoice_id', sa.BigInteger(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), server_default='INR', nullable=False),
        sa.Column('provider', sa.String(length=30), server_default='direct_upi', nullable=False),
        sa.Column('method', sa.String(length=30), server_default='upi', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='created', nullable=False),
        sa.Column('tr_ref', sa.String(length=64), nullable=False),
        sa.Column('upi_intent_url', sa.Text(), nullable=True),
        sa.Column('bank_utr', sa.String(length=64), nullable=True),
        sa.Column('utr_submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', sa.BigInteger(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fee_payment_id', sa.BigInteger(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=100), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['enrolment_id'], ['enrolments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['fee_invoices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['fee_payment_id'], ['fee_payments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('school_id', 'order_no', name='uq_payment_order_no'),
        sa.UniqueConstraint('school_id', 'tr_ref', name='uq_payment_order_tr'),
        sa.UniqueConstraint('idempotency_key', name='uq_payment_order_idempotency'),
    )
    op.create_index('ix_payment_orders_school_id', 'payment_orders', ['school_id'])
    op.create_index('ix_payment_orders_enrolment_id', 'payment_orders', ['enrolment_id'])
    op.create_index('ix_payment_orders_student_id', 'payment_orders', ['student_id'])
    op.create_index('ix_payment_orders_invoice_id', 'payment_orders', ['invoice_id'])
    op.create_index('ix_payment_orders_bank_utr', 'payment_orders', ['bank_utr'])
    op.create_index('ix_payment_orders_status', 'payment_orders', ['status'])
    op.create_index('ix_payment_orders_fee_payment_id', 'payment_orders', ['fee_payment_id'])


def downgrade() -> None:
    op.drop_index('ix_payment_orders_fee_payment_id', table_name='payment_orders')
    op.drop_index('ix_payment_orders_status', table_name='payment_orders')
    op.drop_index('ix_payment_orders_bank_utr', table_name='payment_orders')
    op.drop_index('ix_payment_orders_invoice_id', table_name='payment_orders')
    op.drop_index('ix_payment_orders_student_id', table_name='payment_orders')
    op.drop_index('ix_payment_orders_enrolment_id', table_name='payment_orders')
    op.drop_index('ix_payment_orders_school_id', table_name='payment_orders')
    op.drop_table('payment_orders')
