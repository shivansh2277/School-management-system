"""cheque dishonour and general ledger

Revision ID: e9f8a7b6c5d4
Revises: b3c4d5e6f7a8
Create Date: 2026-11-06 18:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9f8a7b6c5d4'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create general_ledger table
    op.create_table(
        'general_ledger',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('school_id', sa.BigInteger(), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=False),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('account_code', sa.String(length=50), nullable=False),
        sa.Column('account_name', sa.String(length=100), nullable=False),
        sa.Column('debit', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('credit', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'),
        sa.Column('narration', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_general_ledger_school_id', 'general_ledger', ['school_id'])
    op.create_index('ix_general_ledger_reference_type', 'general_ledger', ['reference_type'])
    op.create_index('ix_general_ledger_reference_id', 'general_ledger', ['reference_id'])
    op.create_index('ix_general_ledger_account_code', 'general_ledger', ['account_code'])


def downgrade() -> None:
    op.drop_index('ix_general_ledger_account_code', table_name='general_ledger')
    op.drop_index('ix_general_ledger_reference_id', table_name='general_ledger')
    op.drop_index('ix_general_ledger_reference_type', table_name='general_ledger')
    op.drop_index('ix_general_ledger_school_id', table_name='general_ledger')
    op.drop_table('general_ledger')
